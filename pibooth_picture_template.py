# -*- coding: utf-8 -*-

"""Pibooth plugin to customize the final picture layout using Flowchart Maker."""

import zlib
import base64
import os.path as osp
from io import BytesIO
from urllib.parse import unquote
from xml.etree import ElementTree
from PIL import Image, ImageDraw, ImageFont

import pibooth
from pibooth import fonts
from pibooth.utils import LOGGER
from pibooth import pictures
from pibooth.pictures.factory import PilPictureFactory


__version__ = "1.1.0"


@pibooth.hookimpl
def pibooth_configure(cfg):
    """Declare the new configuration options."""
    cfg.add_option('PICTURE', 'template', 'picture_template.xml',
                   "Pictures template path, it should contain 8 pages (4 capture numbers and 2 orientations)")


@pibooth.hookimpl
def pibooth_reset(cfg, hard):
    """Restore default template file."""
    template_path = cfg.getpath('PICTURE', 'template')
    if template_path and (hard or not osp.isfile(template_path)):
        LOGGER.info("Generate picture template file in '%s'", template_path)
        with open(template_path, 'w') as fp:
            fp.write(DEFAULT)


@pibooth.hookimpl
def pibooth_setup_picture_factory(cfg, factory):
    """Setup :py:class:`TemplatePictureFactory` if a template path is given."""
    if cfg.getpath('PICTURE', 'template'):

        if not getattr(cfg, 'template', None):
            cfg.template = TemplateParser(cfg.getpath('PICTURE', 'template'))

        orientation = cfg.get('PICTURE', 'orientation')
        if orientation == pictures.AUTO:
            orientation = cfg.template.get_best_orientation(factory._images)

        return TemplatePictureFactory(cfg.template, orientation, *factory._images)


def px(cin, dpi=600):
    """Convert a dimension in centiinch into pixels.

    :param cin: dimension in centiinch
    :type cin: str, float, int
    :param dpi: dot-per-inch
    :type dpi: int
    """
    return int(float(cin) * dpi / 100)


class TemplateParserError(Exception):
    pass


class TemplateParser(object):

    """Class to parse a picture template.

    A template is based on a XML file generated with Flowchart Maker (formerly draw.io)
    at https://app.diagrams.net.
    """

    def __init__(self, filename):
        self.filename = filename
        self.data = self.parse()

    def inflate(self, data, b64=False):
        """Decompress the data using zlib.

        In ~2016 Flowchart Maker started compressing 'using standard deflate'
        https://about.draw.io/extracting-the-xml-from-mxfiles
        """
        if b64:  # Optional, additionally base64 decode
            data = base64.b64decode(data)
        return unquote(zlib.decompress(data, -15).decode('utf8'))

    def parse(self):
        """Parse the XML template file.

        :return: data dictionary
        :rtype: dict
        """
        data = {}
        LOGGER.info('Parsing pictures template file: %s', self.filename)
        doc = ElementTree.parse(self.filename).getroot()

        for diagram in doc.iter('diagram'):

            if not list(diagram) and diagram.text.strip():  # Compressed
                template = ElementTree.fromstring(
                    self.inflate(diagram.text, True))
            else:
                template = diagram.find('mxGraphModel')

            template.set('name', diagram.get('name'))
            dpi = int(template[0][0].get('dpi', 600))
            size = (px(template.attrib['pageWidth'], dpi), px(
                template.attrib['pageHeight'], dpi))
            orientation = pictures.PORTRAIT if size[0] < size[1] else pictures.LANDSCAPE

            shapes = []
            distinct_capture_count = set()
            for cell in template.iter('mxCell'):
                shape = TemplateShapeParser(cell, dpi)

                if shape.type == TemplateShapeParser.TYPE_UNKNOWN:
                    continue

                if shape.type == TemplateShapeParser.TYPE_CAPTURE:
                    # Take only captures with a correct number
                    if shape.text in ("1", "2", "3", "4"):
                        shapes.append(shape)
                        distinct_capture_count.add(shape.text)
                    else:
                        LOGGER.warning("Template capture holder with text '%s' ignored", shape.text)

                elif shape.type == TemplateShapeParser.TYPE_TEXT:
                    # Take only text with a correct number
                    if shape.text in ("1", "2", "footer_text1", "footer_text2"):
                        shape.text = shape.text[-1]  # Keep ony index value
                        shapes.append(shape)
                    else:
                        LOGGER.warning("Template text holder with text '%s' ignored", shape.text)

                else:
                    shapes.append(shape)

                # If shape is on the left or the right of the page
                if shape.x + shape.width <= 0 or shape.x >= size[0]:
                    LOGGER.warning("Template shape '%s' X-position out of bounds, try to auto-adjust", shape.text)
                    shape.x = shape.x % size[0]

                # If shape is above or below the page
                if shape.y + shape.height <= 0 or shape.y >= size[1]:
                    LOGGER.warning("Template shape '%s' Y-position out of bounds, try to auto-adjust", shape.text)
                    shape.y = shape.y % size[1]

            # Create template parameters dictionary
            subdata = data.setdefault(orientation, {}).setdefault(
                len(distinct_capture_count), {})
            if subdata:
                raise TemplateParserError(
                    "Several templates with {} captures are defined".format(len(distinct_capture_count)))
            subdata['shapes'] = shapes
            subdata['size'] = size
            subdata['orientation'] = orientation

            # Calculate the orientation majority for this template
            captures = [shape for shape in shapes if shape.type ==
                        TemplateShapeParser.TYPE_CAPTURE]
            texts = [shape for shape in shapes if shape.type ==
                     TemplateShapeParser.TYPE_TEXT]
            portraits = [
                shape for shape in shapes if shape.width < shape.height]
            if len(portraits) * 1.0 / len(captures) >= 0.5:
                subdata['captures_orientation'] = pictures.PORTRAIT
            else:
                subdata['captures_orientation'] = pictures.LANDSCAPE

            LOGGER.info("Found template '%s': %s captures - %s texts - %s others", template.get('name'),
                        len(captures), len(texts), len(shapes) - (len(captures) + len(texts)))

        if not data:
            raise TemplateParserError(
                "No template found in '{}'".format(self.filename))
        return data

    def get(self, key, capture_number, orientation=pictures.PORTRAIT):
        """Return the value of the 'key' info for the given caputures numbers and orientation.

        :param key: key info to get
        :type key: str
        :param capture_number: number of captures to assemble
        :type capture_number: int
        :param orientation: 'portrait' or 'landscape'
        :type orientation: str
        """
        assert orientation in (pictures.PORTRAIT, pictures.LANDSCAPE)
        if orientation not in self.data:
            raise TemplateParserError(
                "No template for '{}' orientation".format(orientation))
        if capture_number not in self.data[orientation]:
            raise TemplateParserError(
                "No template for '{}' captures (orientation={})".format(capture_number, orientation))
        return self.data[orientation][capture_number][key]

    def get_best_orientation(self, captures):
        """Return the best orientation (PORTRAIT or LANDSCAPE), depending on the
        orientation of the given captures and available templates.

        It use the size of the first capture to determine the orientation (all captures
        of a same sequence should have the same orientation).

        :param captures: list of captures to concatenate
        :type captures: list
        :return: orientation PORTRAIT or LANDSCAPE
        :rtype: str
        """
        nbr = len(captures)
        if captures[0].size[0] < captures[0].size[1]:
            captures_orientation = pictures.PORTRAIT
        else:
            captures_orientation = pictures.LANDSCAPE

        for orientation in self.data:
            if nbr in self.data[orientation]:
                if self.data[orientation][nbr]['captures_orientation'] == captures_orientation:
                    return orientation

        for orientation in self.data:
            if nbr in self.data[orientation]:
                return orientation

        return pictures.PORTRAIT

    def get_size(self, capture_number, orientation=pictures.PORTRAIT):
        """Return total size of the final picture in pixels.

        :param capture_number: number of captures to assemble
        :type capture_number: int
        :param orientation: 'portrait' or 'landscape'
        :type orientation: str
        """
        return self.get('size', capture_number, orientation)

    def get_rects(self, capture_number, orientation=pictures.PORTRAIT):
        """Return the list of top-left coordinates and max size rectangle.

        :param capture_number: number of captures to assemble
        :type capture_number: int
        :param orientation: 'portrait' or 'landscape'
        :type orientation: str
        """
        return self.get('shapes', capture_number, orientation)

    def get_capture_rects(self, capture_number, orientation=pictures.PORTRAIT):
        """Return the list of top-left coordinates and max size rectangle.

        :param capture_number: number of captures to assemble
        :type capture_number: int
        :param orientation: 'portrait' or 'landscape'
        :type orientation: str
        """
        return [shape for shape in self.get_rects(capture_number, orientation) if shape.type == TemplateShapeParser.TYPE_CAPTURE]

    def get_text_rects(self, capture_number, orientation=pictures.PORTRAIT):
        """Return the list of top-left coordinates and max size rectangle.

        :param capture_number: number of captures to assemble
        :type capture_number: int
        :param orientation: 'portrait' or 'landscape'
        :type orientation: str
        """
        return [shape for shape in self.get_rects(capture_number, orientation) if shape.type == TemplateShapeParser.TYPE_TEXT]


class TemplateShapeParser(object):

    TYPE_CAPTURE = 'capture'
    TYPE_TEXT = 'text'
    TYPE_IMAGE = 'image'
    TYPE_UNKNOWN = 'unknown'

    def __init__(self, mxcell_node, dpi):
        self.text = self.parse_text(mxcell_node)
        self.style = self.parse_style(mxcell_node)
        self.image = self.style.get('image')
        self.rotation = -int(self.style.get('rotation', 0))
        self.x, self.y, self.width, self.height = self.parse_geometry(mxcell_node, dpi)

        # Define shape type
        if mxcell_node.get('vertex') == "1" and mxcell_node.get('style').startswith('shape=image'):
            self.type = self.TYPE_IMAGE
        elif mxcell_node.get('vertex') == "1" and mxcell_node.get('style').startswith('text;'):
            self.type = self.TYPE_TEXT
        elif mxcell_node.get('vertex') == "1" and not mxcell_node.get('style').startswith('text;'):
            self.type = self.TYPE_CAPTURE
        else:
            self.type = self.TYPE_UNKNOWN

    def __repr__(self):
        return f"Shape(text='{self.text}', type={self.type})"

    def parse_text(self, mxcell_node):
        """Extarct text.

        :param mxcell_node: 'mxCell' node
        :type mxcell_node: :py:class:`ElementTree.Element`
        """
        try:
            # XML format for font/style can be set in the value
            value = ElementTree.fromstring(str(mxcell_node.get('value'))).text
        except ElementTree.ParseError:
            value = mxcell_node.get('value') or ''
        return value

    def parse_style(self, mxcell_node):
        """Extract style data.

        :param mxcell_node: 'mxCell' node
        :type mxcell_node: :py:class:`ElementTree.Element`
        """
        styledict = {'name': ''}
        if 'style' in mxcell_node.attrib:
            style = [p for p in mxcell_node.attrib['style'].split(';') if p.strip()]
            if '=' not in style[0]:
                styledict['name'] = style.pop(0)
            for key_value in style:
                key, value = key_value.split('=', 1)
                styledict[key] = value
        return styledict

    def parse_geometry(self, mxcell_node, dpi=600):
        """Extract geometry data.

        :param mxcell_node: 'mxCell' node
        :type mxcell_node: :py:class:`ElementTree.Element`
        :param dpi: dot-per-inch
        :type dpi: int
        """
        geometry = mxcell_node.find('mxGeometry')
        if geometry is None:
            x, y, width, height = 0, 0, 0, 0
        else:
            x = px(geometry.get('x', 0), dpi)
            y = px(geometry.get('y', 0), dpi)
            width = px(geometry.attrib.get('width', 0), dpi)
            height = px(geometry.attrib.get('height', 0), dpi)
        return x, y, width, height


class TemplatePictureFactory(PilPictureFactory):

    def __init__(self, template, orientation, *images):
        self.template = template
        self.orientation = orientation
        size = self.template.get_size(len(images), self.orientation)
        super(TemplatePictureFactory, self).__init__(size[0], size[1], *images)

    def _iter_images_rects(self):
        raise NotImplementedError("Not applicable for template")

    def _iter_texts_rects(self, interline=None):
        raise NotImplementedError("Not applicable for template")

    def _image_paste(self, image, dest_image, pos_x, pos_y, angle=None):
        """Paste an image onto an other one with the given rotation angle.

        :param image: PIL image to draw on
        :type image: :py:class:`PIL.Image`
        :param dest_image: PIL image to draw on
        :type dest_image: :py:class:`PIL.Image`
        :param pos_x: X-axis position from left
        :type pos_x: int
        :param pos_y: Y-axis position from top
        :type pos_y: int
        :param angle: rotation angle in degree
        :type angle: int
        """
        width, height = image.size
        if angle:
            image = image.rotate(angle, expand=True)
        dest_image.paste(image,
                         (pos_x + (width - image.width)//2,
                          pos_y + (height - image.height)//2),
                         image if angle is not None else None)

    def _build_matrix(self, image):
        """Draw all shape in the order defined in the template.

        :param image: image to draw on
        :type image: :py:class:`PIL.Image`
        :return: drawn image
        :rtype: :py:class:`PIL.Image`
        """
        for shape in self.template.get_rects(len(self._images), self.orientation):
            if shape.type == TemplateShapeParser.TYPE_CAPTURE:
                index = int(shape.text) - 1
                if len(self._images) <= index:
                    continue  # No image available for this index

                src_image = self._images[index]
                src_image, width, height = self._image_resize_keep_ratio(src_image,
                                                                         shape.width,
                                                                         shape.height,
                                                                         self._crop)
                rect = Image.new('RGBA', (shape.width, shape.height), (255, 0, 0, 0))
                self._image_paste(src_image, rect, (shape.width - width) // 2, (shape.height - height) // 2)
                self._image_paste(rect, image, shape.x, shape.y, shape.rotation)

            elif shape.type == TemplateShapeParser.TYPE_TEXT:
                index = int(shape.text) - 1
                if len(self._texts) <= index:
                    continue  # No text available for this index

                text, font_name, color, align = self._texts[index]
                rect = Image.new('RGBA', (shape.width, shape.height), (255, 0, 0, 0))
                draw = ImageDraw.Draw(rect)
                font = fonts.get_pil_font(text, font_name, shape.width, shape.height)
                _, text_height = font.getsize(text)
                (text_width, _baseline), (offset_x, offset_y) = font.font.getsize(text)

                x = 0
                if align == self.CENTER:
                    x += (shape.width - text_width) // 2
                elif align == self.RIGHT:
                    x += (shape.width - text_width)

                draw.text((x - offset_x // 2, (shape.height - text_height) // 2 - offset_y // 2), text, color, font=font)
                self._image_paste(rect, image, shape.x, shape.y, shape.rotation)

            elif shape.type == TemplateShapeParser.TYPE_IMAGE:
                data = base64.b64decode(shape.image.split(',', 1)[1])
                src_image = Image.open(BytesIO(data))
                src_image = src_image.resize((shape.width, shape.height))
                rect = Image.new('RGBA', (shape.width, shape.height), (255, 0, 0, 0))
                self._image_paste(src_image, rect, 0, 0)
                self._image_paste(rect, image, shape.x, shape.y, shape.rotation)

        return image

    def _build_texts(self, image):
        pass  # Texts are drawn with capture matrix to preserve order defined in template

    def _build_outlines(self, image):
        """Draw outlines for captures and texts which is useful to investigate
        position issues.

        :param image: PIL image to draw on
        :type image: :py:class:`PIL.Image`
        """
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        for shape in self.template.get_rects(len(self._images), self.orientation):
            rect = Image.new('RGBA', (shape.width, shape.height), (255, 0, 0, 0))
            draw = ImageDraw.Draw(rect)
            draw.rectangle(((0, 0), (shape.width - 1, shape.height - 1)), outline='red')
            draw.text((10, 10), shape.text, 'red', font)
            self._image_paste(rect, image, shape.x, shape.y, shape.rotation)


DEFAULT = """<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2020-01-01T00:00:00.000Z" agent="Unknown" etag="XdeKuJMKpnKU0TPbWRqA" version="13.1.14" type="device" pages="8"><diagram id="4RqHqJygrZGB2J5vJ4X9" name="Page-1">zZVRb5swEMc/DY+RwIa0e1xo071MahtNU58mFzvg1XDIMYX008+GI+ARde1DpPEQ2b8zd/b/fyYBTcvuTrO6+A5cqICEvAvoTUDI1fXa/jpwHEASxQPIteQDiiawk28CYYi0kVwcvIUGQBlZ+zCDqhKZ8RjTGlp/2R6UX7VmuViAXcbUkv6U3BQDjcNw4t+EzAusvB4DJRvXIjgUjEM7Q/Q2oKkGMMMInn+7/ZNQsWcrYb8OpavlX8lH5R433c2PdCujl4f0qXl7aurofjUlL7tUKOvGdpjaARbxou9nO51fi8r8q+pY6WOp8XivTDW+2AdzHOXX0FRcuCxhQDdtIY3Y1Sxz0db2m2WFKZ1akR3upVIpKND9uzTsH8ehMjO+7R/LP3g03NWr0EZ0s43iUe8ElMLoo12C0QRtwpYfO6Cd+odSZMWsd+IrhAx7Nj9lJnMTUd1PKE0XSu9t3wn9yx7ILEV31Ff2YDS8iLPazjSvoLIZNkzJvLLTzMoqLN845aS9Ul8xUErOXa2zfvqOX8oi4luURGc8Wp/x6GIWxe9ZRP5nizQYZiS4t1ZfLunZioSJf7HiZOHa6RLNXSOfd81Op29zH5v9v9HbPw==</diagram><diagram id="VBIb-lM5qw3djfguzSXG" name="Page-2">5ZZNj9MwEIZ/TY4rJXFb4EjDfkgIgVoER+SNp4nB8USuu0n59YwTp4mbalkOFRLkUvuZ6Yz9vnbaiGVVe294XX5AASpKY9FG7F2UpknyekUfjhx7skwWPSiMFD5pBFv5EzyMPT1IAfsg0SIqK+sQ5qg15DZg3BhswrQdqrBrzQuYgW3O1Zx+lcKWPV3E8cgfQBal77waAhUfcj3Yl1xgM0HsNmKZQbT9CB+/u/WnseKPpGGX56Wr5VnxQblP7WaZLXn+YDbvU80/fkk+b27G4lWbgSI77vopDXyTIPp8tdP+DWj7u65Dp5eV9tt74uoQir23x0F+gwctwFWJI7ZuSmlhW/PcRRs6cMRKWzm1EhrupFIZKjTdd1ncPY6jthN+1z3EX7g1v6onMBbayUL9Vu8BK7DmSCk+mg4+NeOJOR3ocnJa2JDI/SktTrXSqW1ezz/Qls20Tf8NbW8GHY9nEv49rRczrXd0q8F8oy3Z+ZF2NNR2bw3+gIvqTlTXqKnCmitZaJrmJCwQXzvtJL2w3vpAJYVwvS46Gnp+vQsQePRqblGyumBRsriWRcvnLJrfjP/BojOP2JsrmkTT8Yeui03+LbDbXw==</diagram><diagram id="Wbi_p-jtegIuIsBigMpN" name="Page-3">5ZZNc5swEIZ/Dcd4kATEOcbORy+91J12ppeMgmRQK1gqy8H013eFRUDBk6YzbTOTcjF6Vuxq31cWRGxdHW4Nb8r3IKSOaCwOEbuKKCVkmeGPI91ASHIkhVHCsxFs1A/pYezpXgm5CyZaAG1VE8Ic6lrmNmDcGGjDaVvQYdWGF3IGNjnXc/pZCVseaRLHI38nVVH6ytkQqPgw14NdyQW0E8SuI7Y2APZ4B/df3fpprPk9itjP89o16knyQbmP30VXXl7ld3WXftkQs/pQfDobk1eHtdTox81xiDe+SBB9Pttj/0bW9ldVh0ovS+3be+B6H4q9s90gv4F9LaTLEkds1ZbKyk3DcxdtccchK23l1CJ4u1Var0GD6Z9lcX85DrWd8Jv+Qm7AcqugRpykOH5hq36VD9JYeZgs3Ld+K6GS1nQ4xUfPjw/4v0Dq+27H7UQyb2w52Up0gNxv4eIxMZ166sX+DeHZTHj6NoUndBlIT86T19Y+mWnP3qb2NI0D7elF9trapzPtt3j8SnOHLdn52eNoqPXOGvgmT6o9caGGGjOsuFaFUzlHYSXyldNO4Zvl0gcqJYSrddLhcA/8K9POaLq4CGxLknhBZsYxcsK45d/yLXvOt/nR9R/6hgfdgmWBcUu2YPM3zZ8yDofjp0sfm3wAsuuf</diagram><diagram id="l_uaaDOC6MnKtH8phZXj" name="Page-4">3ZZPb4IwGMY/DcclQBHdcbrpsmXZwcOOS0crdBZeUuvQffq1UKQVsj8HFyMH0z6t79v+nrcUD83y3ULgMnsCQrkX+mTnoVsvDMeTWP1qYd8IoyBqhFQw0khBJyzZJzWib9QtI3TjTJQAXLLSFRMoCppIR8NCQOVOWwF3s5Y4pT1hmWDeV18YkVmjRr7f6feUpZnJHLcDOW7nGmGTYQKVJaE7D80EgGxa8Pau1x/6HL8phPU8g65kR8FbcnixXomX+cPz7fMaJ0mwnD+Kqy54vptRrtyYN13VMEmc0e+jHfYvaCF/ytpm+l1os70PzLcu7I3ct/gFbAtCdRTfQ9MqY5IuS5zo0UrVm9IymWtagWquGOcz4CDq/yK/frQOhbT0ef0oXYDEkkFhov9yp2aRH1RIurPWbXa+oJBTKfZqihltK8CcgKjtV109BW25Z1YtBbERsanh9BA6tE01tP9AHvXIhxdJPohG54Y+6qFHF4k+HJ9d1Y966KPLRO+SHwAfTgbAo9GpwMc98Ct17VHxqjYk++98rbqgN1LAmg6itiwooFARppizVCNOFFaq9Kkmx9SNfmMGckaIzjVor1sAlmNX1yd9Ux0dl8MpsFw7GGS7Nj6VaePvTOtfF+dp2j8eMzQZcCweOmd/d0x1uw/Fesz62EZ3Xw==</diagram><diagram id="9yFjgTmBI_ms0_62qLtN" name="Page-5">zZVRb9sgEMc/jR8rEZOk7eOStZ26VeqUSZX6MhFzsekwZxESO/v0AxtiXEdd+xCpfojgd/gO/v/DSeiybO40q4oH5CCTlPAmoV+TNL28mttfBw4dmE2mHci14B2a9GAl/oKHxNOd4LAdLDSI0ohqCDNUCjIzYExrrIfLNiiHVSuWwwisMibH9ElwU3R0TkjPv4HIC195GgIlC2s92BaMYx0hepPQpUY03QjXL27/KZFsbSVs13npKvGqalBujeT51/cnDs/7x+bH9U+d3quLPnnZLEFaN267qR34IoPo29mO59egzP+qhkrvS+2Pt2dyNxR7aw5Bfo07xcFlIQld1IUwsKpY5qK17TfLClM6tSZ2uBFSLlGibt+lpH0cR2Uifts+lr/zaH5Xe9AGmmij/qh3gCUYfbBLQjR47ns+TOu+gaZzz4qoeWhoeuabNj+mTmMXvbwfkJqOpN7YxgP9257IjFV3dCjt1mj8AyfFjURXqGyGBZMiV3aaWV3B8oWTTtg79cUHSsG5q3XS0KHlGg0zAt1bF9fkjKa57LFpEzp27WhQ7NrVuUybvmVa+plNO5dHr+4VnY0tmp28WB+3yE77b3Mbi/7f6M0/</diagram><diagram id="N6H1taoqGx8Z-k8xFQ1X" name="Page-6">5ZZNc5swEIZ/DcfMAMJ2rrXrpIekM40P7fTSkdEa1AqWkeVg+uu7AmFQYPJxSA8tB0Z6Vt6V3leyCNimON9qXuX3KEAFcSjOAfsYxPHqeklvC5oOLKKkA5mWokPRAHbyNzgYOnqSAo7eQIOojKx8mGJZQmo8xrXG2h92QOVXrXgGE7BLuZrSr1KYvKPLMBz4J5BZ7ionfaDg/VgHjjkXWI8Q2wZsoxFN18L9Tzv/OFR8TxK245x0lXxStVfubouYfjdf9kXzcPgsI1Osv10NyYvzBhS5cdN1qeGKeNHns13Wr6E0L1XtK70utVveI1cnX+yjaXr5NZ5KATZLGLB1nUsDu4qnNlrTfiOWm8KqFVHzIJXaoELd/paF7WM5lmbEb9qH+CuX5mb1CNrAeTRRt9RbwAKMbmiIi/aWN363HvYPY47lo70T9/Zyt2ezS+Z4bKJT9w1Ks4nS8T+i9BOpo8WM1ss5rdl7aZ1MtD7QGQf9g5ZkphvcUl/bo9H4C2bVHaleYkkZ1lzJrKRuSsIC8bXVTtLf1wcXKKQQttaso77nf+s4JFOPousZj6LkvTxaPOfR9Gj8Bx6xlW/SaurR5UrOvfvuzRZRd7j12tjoy4Ft/wA=</diagram><diagram id="Y-HRS4QSfgI3UBn2UQzj" name="Page-7">5ZZRb5swEMc/DY+RDCZR87hkTSqt06pG26S9RC52wKvhkHFKsk+/M5iCS9SlD9GklpeY/x13vt+ZCwFd5oe1ZmX2FbhQQUT4IaCfgygK6dUMf6xybJV5GLdCqiV3Tr2wkX+EE4lT95KLynM0AMrI0hcTKAqRGE9jWkPtu+1A+VlLloqRsEmYGqs/JTdZq84I6fUbIdPMZY47Q846XydUGeNQDyR6HdClBjDtCh5+2/1HRLEHZNj4OXSlfJG1I7f58et2z7/dre/rL8dwu1Wr6vukD54flkJhO1btLS5cEs/6erTn+rUozL+ydpnOC+3Ke2Jq78OuzLHDr2FfcGGjkIAu6kwasSlZYq01HjjUMpNbWiEud1KpJSjQzbOUNJfVoTADfdVcqGswzEgoUJ6EUxTOrNVt80loIw6Dnbva1wJyYfQRXZx1Es7bR9xL0JVe9ycqunK9zQanKexE5k5x+hw6GrbV8X4DezpiH71T9tGc+Oy7yTKAT8kJ+BG5FPx4BJ++U/gYfMg+nIf/m/10xH6HI1joLVZkxvPHqj7rymh4FCdpD7pQQIERFkzJ1FJOkKtAfWHRSfx3+eQMueTc5jrZYf8MXKpHdOq/IFjReDrFp6bTxZo0e61J40H1AZtE4zObRN/eI7ztP0sa2+Dbjl7/BQ==</diagram><diagram id="eN_dZz7XeTnDUXszf6p8" name="Page-8">5ZZNb+MgEIZ/jY8rYeMk7bHJNu1K7SmVeqyoIYYGG4uQ2tlfv4ONY7NY/Th0VWV9sOAdPAPPDOAIr4rmRpOK3yvKZJQg2kT4Z5Qki4s5vK1w7IRZnHZCrgXtpHgQNuI3cyJy6kFQtvcGGqWkEZUvZqosWWY8jWitan/YVkk/akVyFgibjMhQfRTU8E6dIzTot0zk3EVOe0NB+rFO2HNCVT2S8HWEV1op07XU84udf4IkeQaE7TiHrhJ/Re3J3Td89mtRXNzR3d3T5YNY73jyY3BeNCsmIRvrrgsNF8Szvu3ttH7NSvNe1D7Sx1y75b0SefBh782xx6/VoaTMekERXtZcGLapSGatNdQbaNwUllYMza2QcqWk0u23GLWP1VVpRvq6fUD/4NLcrF6ZNqwZTdQt9Yapghl9hCHO2qfclTzkrevXQwHFC6fxUfHE/YfEFW1+cp2Ms+jwfgI1DlAnZ4I6nn031mnAGp8H6zT+dnU9C1in58EaLhKfdYgapxOoky9DPQ9Qb+HuYvoJVmTCg9uqPtq90WrHJuGOoJeqBA9LIkVeQjcDrgz0pUUn4Fq+coZCUGpjTSbUT/k/OuYndkOCpnYD+qoULd5KUXjg/38pOp1O7+UIfz5F0B1+5lrb6IcYX/8B</diagram></mxfile>
"""
