# -*- coding: utf-8 -*-

import Image, StringIO, os

class ImageReducer (object, ) :
    def __init__ (self, imagedata, filename, ) :
        self._fn = StringIO.StringIO(imagedata, )
        self._fn.name = os.path.basename(filename, )
        self._im = Image.open(self._fn, )

    def _get_mimetype (self, name, ) :
        from http import _mimetypes
        return _mimetypes.EXTENSIONS.get(os.path.splitext(name, )[1][1:].lower())

    def reduce (self, quality=30, ) :
        _fn = StringIO.StringIO()

        # reset the quality fo JPEG.
        if self._im.format in ("JPG", "JPEG", ) :
            _fn.name = "1.jpg"
            self._im.save(_fn, quality=quality, )
        elif self._im.format in ("PNG", ) :
            if "A" not in self._im.mode :
                _fn.name = "1.jpg"
                self._im.save(_fn, quality=quality, )
            else :
                _fn.name = "1.gif"
                _mask = Image.eval(self._im.split()[3], lambda a: 255 if a <=128 else 0)
                self._im.convert("RGB").convert(
                    "P", palette=Image.ADAPTIVE, colors=255,
                ).paste(255, _mask, )

                self._im.save(_fn, transparency=255, )
        else :
            _fn.name = self._fn.name
            self._im.save(_fn, )

        if len(_fn.getvalue()) > len(self._fn.getvalue()) :
            _fn = StringIO.StringIO(self._fn.getvalue(), )
            _fn.name = self._fn.name
            
        _fn.seek(0, 0, )
        return (
            _fn,
            self._get_mimetype(_fn.name, ),
        )


if __name__ == "__main__" :
    def reduce_size (imagedata, filename, ) :
        return ImageReducer(imagedata, filename, ).reduce(30, )

    def print_info (im) :
        im.fp.seek(0, 0, )
        _d = im.fp.read()
        _orig = len(_d)
        print "               name:", im.filename
        print "             format:", im.format
        print "               mode:", im.mode
        print "               info:", im.info.keys()
        print "               size:", _orig
        im.fp.seek(0, 0, )
        print "           size new:", reduce_size(_d, im.filename, )[0].len
        print "           mimetype:", reduce_size(_d, im.filename, )[1]

        _new = reduce_size(_d, im.filename, )[0].len

        print "        compression:", "%0.1f%%" % (100 - (float(_new) / float(_orig) * 100), )
        print

    ##################################################
    # downsize the image.

    # png, none-transparent
    _name = "tests/png-whitebackground-500.png"
    _im = Image.open(_name, )
    print_info(_im)

    _name = "tests/png-transparent-500.png"
    _im = Image.open(_name, )
    print_info(_im)

    _name = "tests/jpg-500.jpg"
    _im = Image.open(_name, )
    print_info(_im)

    _name = "tests/no-transparency.png"
    _im = Image.open(_name, )
    print_info(_im)

    _name = "tests/bigger.png"
    _im = Image.open(_name, )
    print_info(_im)


