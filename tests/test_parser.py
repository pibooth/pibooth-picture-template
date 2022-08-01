# -*- coding: utf-8 -*-


import os
import os.path as osp
import pytest
import pygame
from pibooth_picture_template import TemplateParser, TemplateParserError


HERE = osp.dirname(osp.abspath(__file__))
TEMPLATES = [osp.join(HERE, 'data', name) for name in os.listdir(osp.join(HERE, 'data'))]


@pytest.mark.parametrize("nbr", (1, 2, 3, 4))
@pytest.mark.parametrize("template", TEMPLATES)
def test_capture_text(nbr, template):
    parser = TemplateParser(template)
    if template.endswith('template3.xml') and nbr in (1, 4):
        # No template defined for 1 and 4 captures
        with pytest.raises(TemplateParserError):
            parser.get_capture_rects(nbr)
        with pytest.raises(TemplateParserError):
            parser.get_text_rects(nbr)
    elif template.endswith('symetric_template.xml'):
        assert len(parser.get_capture_rects(nbr)) == nbr * 2, "Excepecting 2 times more pictures to be captured"
        assert len(parser.get_text_rects(nbr)) == 2 * 2, "Excepecting 2 times more texts to be captured"
    elif template.endswith('other_forms.xml'):
        assert len(parser.get_capture_rects(nbr)) == nbr
        assert len(parser.get_text_rects(nbr)) >= 1
    else:
        assert len(parser.get_capture_rects(nbr)) == nbr
        assert len(parser.get_text_rects(nbr)) == 2


@pytest.mark.parametrize("nbr", (1, 2, 3, 4))
@pytest.mark.parametrize("template", TEMPLATES)
def test_capture_positions(nbr, template):
    parser = TemplateParser(template)
    if template.endswith('template3.xml') and nbr in (1, 4):
        return  # No template defined for 1 and 4 captures

    for rect in parser.get_capture_rects(nbr):
        rect = pygame.Rect(*rect[:4])
        assert rect.colliderect(pygame.Rect(0, 0, *parser.get_size(nbr)))


@pytest.mark.parametrize("nbr", (1, 2, 3, 4))
@pytest.mark.parametrize("template", TEMPLATES)
def test_text_positions(nbr, template):
    parser = TemplateParser(template)
    if template.endswith('template3.xml') and nbr in (1, 4):
        return  # No template defined for 1 and 4 captures

    for rect in parser.get_text_rects(nbr):
        rect = pygame.Rect(*rect[:4])
        assert rect.colliderect(pygame.Rect(0, 0, *parser.get_size(nbr)))
