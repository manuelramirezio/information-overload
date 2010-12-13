# -*- coding: utf-8 -*-

import os, datetime, pysvn, logging, StringIO, uuid

from django.conf import settings
from django.db import models
from django.db.models import Max, manager, ObjectDoesNotExist, Q
from django.contrib.auth import models as models_auth
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.files.storage import FileSystemStorage

from django_modules.db.models.query import translate_query

from IO.common import models as models_common
from IO.developer import models as models_developer
from IO.project import models as models_project
from IO.dialog import models as models_dialog

from spikeekips import _mimetypes

import utils as utils_version_control

TEXT_MIMETYPES = _mimetypes.TEXT.keys()
TEXT_MIMETYPES_EXTS = list()
map(TEXT_MIMETYPES_EXTS.extend, _mimetypes.TEXT.itervalues(), )

FILE_FIELD_TYPE_REGULAR = u"regular"
FILE_FIELD_TYPE_DIRECTORY = u"directory"
FILE_FIELD_TYPE_SYMLINK = u"symlink"
FILE_FIELD_TYPE_EXEC = u"exec"

CHOICES_FILETYPE = (
    (FILE_FIELD_TYPE_REGULAR,   u"Regular File", ),
    (FILE_FIELD_TYPE_DIRECTORY, u"Directory", ),
    (FILE_FIELD_TYPE_SYMLINK,   u"Symbolic Link", ),
    (FILE_FIELD_TYPE_EXEC,      u"Executable", ),
)
DICT_CHOICES_FILETYPE = dict(CHOICES_FILETYPE)

REVISION_FILE_KIND_ADDED    = u"added"
REVISION_FILE_KIND_MODIFIED = u"modified"
REVISION_FILE_KIND_DELETE   = u"delete"

CHOICES_REVISION_FILE_KIND = (
    (REVISION_FILE_KIND_ADDED,      u"Added", ),
    (REVISION_FILE_KIND_MODIFIED,   u"Modified", ),
    (REVISION_FILE_KIND_DELETE,     u"Deleted", ),
)
DICT_CHOICES_REVISION_FILE_KIND = dict(CHOICES_REVISION_FILE_KIND)


class Info (models.Model, ) :
    class Meta :
        unique_together = ("project", "name", )

    name = models.CharField(max_length=100, )
    project = models.ForeignKey(models_project.Item,
        related_name="version_control", )

    repository_url = models.CharField(max_length=400, )

    time_started = models.DateTimeField(auto_now_add=True)
    time_updated = models.DateTimeField(auto_now=True, )

    def __unicode__ (self, ) :
        return u"VersionControl for '%s'" % self.project

    @classmethod
    def signal_callback_post_save (self, *a, **kw) :
        if kw.get("created") :
            # create root file
            File.objects.get_or_create(
                uid=File.get_uid(None, filetype=FILE_FIELD_TYPE_DIRECTORY, ),
                info=kw.get("instance"),
                parent=None,
                filetype=FILE_FIELD_TYPE_DIRECTORY,
            )

        return

    @property
    def root (self, ) :
        return File.objects.get(
            info=self,
            parent=None,
            filetype=FILE_FIELD_TYPE_DIRECTORY,
        )

    @property
    def repository_path (self, ) :
        return get_repository_path(self.project.code, self.name, )

    @property
    def participants (self, ) :
        #return self.authors.filter(profile__isnull=False, )
        return self.authors.all()

    @property
    def latest_revision (self, ) :
        _qs = self.revision.all()
        if _qs.count() < 1 :
            return None

        return _qs.order_by("-number")[0]

    ##################################################
    # SVN
    def svn_update (self, revision_number=0, ) :
        import pysvn
        _client = pysvn.Client()
        try :
            _number = _client.update(
                self.repository_path,
                recurse=True,
                revision=pysvn.Revision(
                    pysvn.opt_revision_kind.number,
                    revision_number,
                ),
            )[0].number
        except pysvn.ClientError :
            import traceback
            traceback.print_exc()
            return None

        if _number < 0 :
            raise RuntimeError(u"This repository path does not exist" % self.repository_path, )

        return _number

    def checkout (self, revision_number=1, ) :
        import pysvn

        logging.debug(u"Checkout from repository, '%s' to '%s'" % (
                self.repository_url,
                os.path.relpath(self.repository_path),
            ),
        )

        _client = pysvn.Client()
        try :
            _client.checkout(
                self.repository_url,
                self.repository_path,
                revision=pysvn.Revision(pysvn.opt_revision_kind.number, revision_number, ),
            )
        except pysvn.ClientError, e :
            raise RuntimeError(e, )

        logging.debug("Successfully checked out from repository, '%s' to '%s'" % (
                self.repository_url,
                os.path.relpath(self.repository_path),
            ),
        )

        return

    def revision_update (self, revision_number=None, ) :
        import pysvn

        # get the latest updated revision.
        _qs = Revision.objects.filter(
            info__project=self.project,
        ).order_by("-number")
        if _qs.count() < 1 :
            _latest_number = 0
        else :
            _latest_number = _qs[0].number

        if revision_number and _latest_number > revision_number :
            logging.info(u"Already updated to %d" % revision_number, )
            return (_latest_number, None, )

        _client = pysvn.Client()

        logging.info(u"Updating revision from %s" % _latest_number, )

        _revision_number = _latest_number
        _updated_number = None
        while True :
            _revision_number += 1
            if revision_number and _revision_number > revision_number :
                break

            logging.info(u"Updating revision to %s" % _revision_number, )
            _n = self.svn_update(_revision_number, )
            if _n is None :
                break

            _updated_number = _n

            # get revision info
            try :
                _logs = _client.log(
                    self.repository_path,
                    pysvn.Revision(pysvn.opt_revision_kind.number, _revision_number, ),
                    pysvn.Revision(pysvn.opt_revision_kind.number, _revision_number, ),
                )
            except pysvn.ClientError, e : # revision not found in this repository
                break

            _info = dict()
            if len(_logs) > 0 :
                _info = _logs[0]

            # get developer
            _author = None
            if _info.get("author", "").strip() :
                (_author, _created, ) = Author.objects.get_or_create(
                    info=self,
                    name=_info.get("author").strip(),
                )

            _time_commit = None
            if _info.get("date") :
                try :
                    _time_commit = datetime.datetime.fromtimestamp(_info.get("date"), )
                except :
                    pass

            # create revision
            (_revision, _created, ) = Revision.objects.get_or_create(
                info=self,
                number=_revision_number,
                author=_author,
                log=_info.get("message"),
                time_commit=_time_commit,
            )

            try :
                _d = _client.diff_summarize(
                    self.repository_path,
                    pysvn.Revision(pysvn.opt_revision_kind.number, _revision_number - 1, ),
                    self.repository_path,
                    pysvn.Revision(pysvn.opt_revision_kind.number, _revision_number, ),
                )
            except pysvn.ClientError :
                continue

            _count = 1
            for j in _d :
                _filename = j.path

                logging.info("\t> %d: (%d/%d) updating '%s'" % (
                        _revision_number,
                        _count, len(_d),
                        _filename,
                    ),
                )
                _count += 1

                # create or get the File
                (_file, _created,
                        ) = File.objects.get_or_create_with_abspath(
                    info=self,
                    abspath=_filename,
                    filetype=File.get_filetype_from_pysvn(j, ),
                )

                if j.node_kind not in (pysvn.node_kind.file, ) :
                    continue
                elif RevisionFile.get_kind(j, ) == REVISION_FILE_KIND_DELETE :
                    continue

                _content_file = None
                try :
                    _content = _client.cat(
                        os.path.join(self.repository_path, j.path, ),
                        pysvn.Revision(
                            pysvn.opt_revision_kind.number, _revision_number,
                        ),
                    )
                except :
                    continue

                try :
                    # check this file is readable as text or not
                    _plist = _client.proplist(
                        os.path.join(
                            self.repository_url,
                            j.path,
                        ),
                        revision=pysvn.Revision(
                            pysvn.opt_revision_kind.number, _revision_number, ),
                    )
                except :
                    import traceback
                    traceback.print_exc()
                    print j.items()
                    raise

                _mimetype = None
                if len(_plist) > 0 :
                    (_none, _pdict, ) = _plist[0]
                    if _pdict.get("svn:mimetype") in TEXT_MIMETYPES :
                        _mimetype = _pdict.get("svn:mimetype")

                if not _mimetype :
                    _ext = os.path.splitext(_filename)[1][1:]
                    _mimetype = _mimetypes.EXTENSIONS.get(_ext, )

                _content_file = InMemoryUploadedFile(
                    StringIO.StringIO(_content, ),
                    "content",
                    str(uuid.uuid1(), ),
                    _mimetype,
                    len(_content, ),
                    None,
                )

                if not _mimetype :
                    _mimetype = "text/plain"

                if _file.mimetype != _mimetype :
                    _file.mimetype = _mimetype
                    _file.save()

                logging.info("\t< register '%s' to system." % _filename, )

                # create or get the RevisionFile
                (_revision_file, _created,
                        ) = RevisionFile.objects.get_or_create(
                    revision=_revision,
                    file=_file,
                    content=_content_file,
                    kind=unicode(j.summarize_kind),
                )

        return (_latest_number, _updated_number, )

class Author (models.Model, ) :
    class Meta :
        unique_together = ("info", "name", )

    info = models.ForeignKey(Info, related_name="authors", )
    name = models.CharField(max_length=255, )
    profile = models.ForeignKey(models_developer.Profile,
        related_name="version_control_profiles", blank=True, null=True, )

    def __unicode__ (self, ) :
        return self.name

class FileManager (manager.Manager, ) :
    def get_or_create_with_abspath (self, *a, **kw) :
        _abspath = kw.get("abspath", "").strip()
        if not _abspath :
            raise ValueError(u"`abspath` must be provided.")

        _dirnames = [i for i in os.path.dirname(_abspath, ).split("/") if i.strip()]
        _info = kw.get("info", )

        _parent = _info.root

        try :
            _parent = self.get_by_path(
                kw.get("info"),
                "/".join(_dirnames),
                FILE_FIELD_TYPE_DIRECTORY,
            )
        except ObjectDoesNotExist :
            # get or create directory (filetype="directory", ) recursivly.
            for i in ["/".join(_dirnames[:i]) for i in range(len(_dirnames) + 1) if i > 0] :
                (_parent, _created, ) = super(FileManager, self).get_or_create(
                    uid=self.model.get_uid(i, filetype=FILE_FIELD_TYPE_DIRECTORY, ),
                    info=kw.get("info"),
                    name=os.path.basename(i),
                    abspath=i,
                    filetype=FILE_FIELD_TYPE_DIRECTORY,
                    parent=_parent,
                )

        kw["name"] = os.path.basename(_abspath, )
        kw["parent"] = _parent
        kw["uid"] = self.model.get_uid(_abspath, filetype=kw.get("filetype"), )

        return super(FileManager, self).get_or_create(*a, **kw)

    def get_by_path (self, info, abspath, filetype, ) :
        return self.get(
            info=info,
            uid=self.model.get_uid(abspath, filetype=filetype, ),
        )

class File (models_common.ReferenceTag, ) :
    class Meta :
        unique_together = ("info", "parent", "uid", "filetype", )

    objects = FileManager()

    info = models.ForeignKey(Info, related_name="files", )

    uid = models.CharField(max_length=40, ) # basename
    name = models.CharField(max_length=255, blank=True, null=True, ) # basename
    abspath = models.TextField(blank=True, null=True, ) # abspath name
    filetype = models.CharField(
        max_length=10, default=FILE_FIELD_TYPE_REGULAR, choices=CHOICES_FILETYPE, )

    mimetype = models.CharField(max_length=50, )
    parent = models.ForeignKey("self", blank=True, null=True, )

    def __unicode__ (self, ) :
        return u"%s: %s" % (
            DICT_CHOICES_FILETYPE.get(self.filetype, ),
            self.abspath_verbose,
        )

    def _get_reference_tag (self, ) :
        return u"project:%s;vc:%s;f:%s" % (
            self.info.project.code,
            self.info.name,
            self.abspath_verbose,
        )

    @classmethod
    def get_uid (cls, path, filetype="regular", ) :
        import hashlib
        return hashlib.sha1((path and path or "") + "." + filetype).hexdigest()

    @property
    def is_binary (self, ) :
        return self.mimetype not in TEXT_MIMETYPES

    def get_children (self, is_directory=True, ) :
        if self.filetype != FILE_FIELD_TYPE_DIRECTORY :
            return list()

        return self.__class__.objects.filter(
            info=self.info,
            parent=self,
            filetype=FILE_FIELD_TYPE_DIRECTORY,
        )

    def get_children_recursive (self, is_directory=True, ) :
        if self.filetype == FILE_FIELD_TYPE_DIRECTORY :
            for i in self.get_children(is_directory=is_directory, ) :
                yield i

                for j in i.get_children_recursive(is_directory=is_directory, ) :
                    yield j

    @property
    def is_root (self, ) :
        return self.parent is None and self.filetype == FILE_FIELD_TYPE_DIRECTORY

    @property
    def abspath_verbose (self, ) :
        if self.is_root :
            return u"/"

        if self.filetype == FILE_FIELD_TYPE_REGULAR :
            _fmt = u"/%s"
        else :
            _fmt = u"/%s/"

        return _fmt % self.abspath

    @property
    def filetype_verbose (self, ) :
        return DICT_CHOICES_FILETYPE.get(self.filetype, )

    @classmethod
    def get_filetype_from_pysvn (self, diff_summary, ) :
        import pysvn
        _n = diff_summary.node_kind
        if _n == pysvn.node_kind.dir :
            return FILE_FIELD_TYPE_DIRECTORY
        elif _n == pysvn.node_kind.file :
            return FILE_FIELD_TYPE_REGULAR
        elif _n == pysvn.node_kind.none :
            return None

    @classmethod
    def normalize_path (self, path, ) :
        _p = "/".join([i for i in path.strip().split("/") if i.strip()]).strip()

        return _p and _p or None

class Revision (models_common.ReferenceTag, ) :
    class Meta :
        unique_together = ("info", "number", )
        ordering = ("-number", )

    info = models.ForeignKey(Info, related_name="revision", )

    number = models.IntegerField(db_index=True, )
    author = models.ForeignKey(Author, blank=True, null=True, db_index=True,
        related_name="revision", )
    time_commit = models.DateTimeField(db_index=True, blank=True, null=True, )

    log = models.TextField(blank=True, null=True, )

    def __unicode__ (self, ) :
        return u"Revision %s" % (self.number, )

    def _get_reference_tag (self, ) :
        return u"project:%s;vc:%s;r:%d" % (
            self.info.project.code,
            self.info.name,
            self.number,
        )

    @property
    def previous (self, ) :
        _qs = self.__class__.objects.filter(
            info=self.info,
            number__lt=self.number,
        ).order_by("-number")
        if _qs.count() < 1 :
            return None

        return _qs[0]

    @property
    def next (self, ) :
        _qs = self.__class__.objects.filter(
            info=self.info,
            number__gt=self.number,
        ).order_by("number")
        if _qs.count() < 1 :
            return None

        return _qs[0]

    def get_by_number (self, number, ) :
        if number >= self.number :
            return self

        if number < 1 :
            return None

        _qs = self.__class__.objects.filter(
            info=self.info,
            number__lt=self.number,
            number__gte=number,
        )
        if _qs.count() > 0 :
            _revision = _qs.order_by("number", )[0]
        else :
            _qs = self.__class__.objects.filter(
                info=self.info,
                number__lte=number,
            ).order_by("-number")

            if _qs.count() < 1 :
                _revision = None
            else :
                _revision = _qs[0]

        return _revision

    def diff_by_number (self, number, root=None, ) :
        """
        Diff in the side of Revision only support one side, from high revision
        to low revision.
        """
        if number >= self.number :
            return None

        _revision = self.get_by_number(number, )

        if root and root.filetype == FILE_FIELD_TYPE_REGULAR :
            return self.files.get(file=root, ).diff_by_number(number, )

        _q = Q(
            revision_file__revision__info=self.info,
            revision_file__revision__number__gt=_revision and
                _revision.number or self.number -1,
            revision_file__revision__number__lte=self.number,
        )

        return File.objects.filter(_q, ).distinct()

_fs = FileSystemStorage(location=os.path.join(
        settings.VERSION_CONTROL_STORAGE_PATH,
        "revision_file",
    ),
)

class RevisionFileManager (manager.Manager, ) :
    def get_by_number (self, f, number, ) :
        try :
            return self.get(
                file=f,
                revision__info=f.info,
                revision__number=number,
            )
        except ObjectDoesNotExist :
            pass

        _ps = self.filter(
            file=f,
            revision__info=f.info,
            revision__number__lte=number,
        ).order_by("-revision__number", )
        if _ps.count() < 1 :
            return None

        return _ps[0]

class RevisionFile (models_common.ReferenceTag, ) :
    objects = RevisionFileManager()

    class Meta :
        unique_together = ("revision", "file", "kind", )
        ordering = ("revision__number", )

    revision = models.ForeignKey(Revision, related_name="files", )

    file = models.ForeignKey(File, related_name="revision_file", )
    content = models.FileField(
        storage=_fs,
        upload_to="%Y/%m/%d",
        blank=True, null=True,
    )

    kind = models.CharField(max_length=10, choices=CHOICES_REVISION_FILE_KIND, db_index=True, )

    def __unicode__ (self, ) :
        return u"revision %d, file: %s" % (self.revision.number, self.file, )

    def _get_reference_tag (self, ) :
        return u"project:%s;vc:%s;r:%d;f:%s" % (
            self.revision.info.project.code,
            self.revision.info.name,
            self.revision.number,
            self.file.abspath_verbose,
        )

    @property
    def kind_verbose (self, ) :
        return DICT_CHOICES_REVISION_FILE_KIND.get(self.kind, )

    @classmethod
    def get_kind (cls, diff_summary, ) :
        _v = unicode(diff_summary.summarize_kind, ).lower()
        if _v not in DICT_CHOICES_REVISION_FILE_KIND.keys() :
            return REVISION_FILE_KIND_ADDED

        return _v

    @property
    def previous (self, ) :
        _qs = self.__class__.objects.filter(
            revision__info=self.revision.info,
            file=self.file,
            revision__number__lt=self.revision.number,
        ).order_by("-revision__number")

        if _qs.count() < 1 :
            return None

        return _qs[0]

    @property
    def next (self, ) :
        _qs = self.__class__.objects.filter(
            revision__info=self.revision.info,
            file=self.file,
        )

        _qs = self.__class__.objects.filter(
            revision__info=self.revision.info,
            file=self.file,
            revision__number__gt=self.revision.number,
        ).order_by("revision__number")

        if _qs.count() < 1 :
            return None

        return _qs[0]

    @property
    def first (self, ) :
        return self.__class__.objects.filter(file=self.file, ).order_by("revision__number")[0]

    @property
    def last (self, ) :
        return self.__class__.objects.filter(file=self.file, ).order_by("-revision__number")[0]

    def get_revision_by_number (self, number, closest=True, ) :
        if number == self.revision.number :
            return self

        if not closest :
            try :
                return self.__class__.objects.get(
                    file=self.file,
                    revision__info=self.revision.info,
                    revision__number=number,
                )
            except ObjectDoesNotExist :
                return None

        _q = Q(
            file=self.file,
            revision__info=self.revision.info,
        )
        if number > self.revision.number :
            _order_by = "-revision__number"
        else :
            _order_by = "revision__number"

        _ps = self.__class__.objects.filter(_q, ).order_by(_order_by, )
        if _ps.count() < 1 :
            return None

        _object = _ps[0]

        _q = None
        if number > self.revision.number and _object.revision.number < number :
            _q = Q(
                file=self.file,
                revision__info=self.revision.info,
                revision__number__gte=_object.revision.number,
            )
        elif number < self.revision.number and _object.revision.number > number :
            _q = Q(
                file=self.file,
                revision__info=self.revision.info,
                revision__number__lte=_object.revision.number,
            )

        if _q :
            _ps = self.__class__.objects.filter(_q, ).order_by(_order_by, )
            if _ps.count() < 1 :
                return None

            _object = _ps[0]

        return _object

    def diff_by_number (self, number, ) :
        if self.revision.number == number :
            return (None, None, )

        _target_content = self.content and self.content.read().splitlines() or list()
        _source = None
        _source_content = list()

        if self.kind != "added" :
            _source = self.get_revision_by_number(number)
            if _source == self or _source is None :
                _source_content = list()
            else :
                _source_content = _source.content and _source.content.read(
                    ).splitlines() or list()

        return dict(
            revision_file=self,
            revision_to=self.revision,
            revision_from=_source and _source.revision or None,
            diff=utils_version_control.diff_content(_source_content, _target_content, ),
        )


class MessageManager (manager.Manager, ) :
    def _translate (self, q, ) :
        _q = list(q[:])
        _q[0] = "version_control_message__%s" % _q[0]

        return tuple(_q, )

    def get_query_set_for_message (self, content_object, *a, **kw) :
        _q = Q(*a, **kw)
        if content_object :
            _objects = self._parse_content_object(content_object, )
            for k, v in _objects.items() :
                if not v :
                    continue

                _q = _q & Q(**{k: v, })

        return translate_query(
            _q,
            func=self._translate,
        )

    def _parse_content_object (self, content_object, ) :
        _info = _revision = _revision_file = _file = None

        if isinstance(content_object, Info, ) :
            _info = content_object
        elif isinstance(content_object, Revision, ) :
            _info = content_object.info
            _revision = content_object
        elif isinstance(content_object, RevisionFile, ) :
            _info = content_object.revision.info
            _revision = content_object.revision
            _revision_file = content_object
        elif isinstance(content_object, File, ) :
            _info = content_object.info
            _file = content_object

        return dict(
            info=_info,
            revision=_revision,
            revision_file=_revision_file,
            file=_file,
        )

    def get_or_create (self, message, content_object, ) :
        return super(MessageManager, self).get_or_create(
            message=message,
            **self._parse_content_object(content_object, )
        )

class Message (models_dialog.BaseConnectedMessage, ) :
    objects = MessageManager()

    class Meta :
        unique_together = ("info", "revision", "revision_file", "file", "message", )

    message = models.ForeignKey(models_dialog.Message, related_name="version_control_message", )

    info = models.ForeignKey(Info, )
    revision = models.ForeignKey(Revision, blank=True, null=True, )
    revision_file = models.ForeignKey(RevisionFile, blank=True, null=True, )
    file = models.ForeignKey(File, blank=True, null=True, )

##################################################
# Signal handling

models.signals.post_save.connect(
    Info.signal_callback_post_save,
    sender=Info,
)

def get_repository_path (*names) :
    return os.path.join(
        settings.VERSION_CONTROL_STORAGE_PATH,
        "repository",
        ".".join(names, ),
    )


