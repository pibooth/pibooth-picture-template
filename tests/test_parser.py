# -*- coding: utf-8 -*-


import os
import os.path as osp
import pytest
import pygame
from pibooth_picture_template import TemplateParser, TemplateParserError


HERE = osp.dirname(osp.abspath(__file__))
TEMPLATES = []
for name in os.listdir(osp.join(HERE, 'data')):
    base, ext = osp.splitext(name)
    if ext == '.xml':
        numbers = base.rsplit('_', 1)[-1].split('-')
        for nbr in numbers:
            TEMPLATES.append((int(nbr), osp.join(HERE, 'data', name)))


@pytest.mark.parametrize("nbr,template,", TEMPLATES)
def test_capture_text(nbr, template):
    parser = TemplateParser(template)
    if 'symetric_template' in template:
        assert len(parser.get_capture_rects(nbr)) == nbr * 2, "Excepecting 2 times more pictures to be captured"
        assert len(parser.get_text_rects(nbr)) == 3, "Excepecting 3 texts"
    elif 'other_forms' in template or 'shapes_order' in template:
        assert len(parser.get_capture_rects(nbr)) == nbr
        assert len(parser.get_text_rects(nbr)) == 1, "Excepecting 1 text"
    else:
        assert len(parser.get_capture_rects(nbr)) == nbr
        assert len(parser.get_text_rects(nbr)) == 2
    


@pytest.mark.parametrize("nbr,template,", TEMPLATES)
def test_capture_positions(nbr, template):
    parser = TemplateParser(template)

    for rect in parser.get_capture_rects(nbr):
        rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height)
        assert rect.colliderect(pygame.Rect(0, 0, *parser.get_size(nbr)))


@pytest.mark.parametrize("nbr,template,", TEMPLATES)
def test_text_positions(nbr, template):
    parser = TemplateParser(template)

    for rect in parser.get_text_rects(nbr):
        rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height)
        assert rect.colliderect(pygame.Rect(0, 0, *parser.get_size(nbr)))


@pytest.mark.parametrize("nbr,template,", TEMPLATES)
def test_order(nbr, template):
    if 'shapes_order' in template:
        parser = TemplateParser(template)
        index = 1
        for rect in parser.get_rects(nbr):
            assert rect.text == str(index)
            index += 1