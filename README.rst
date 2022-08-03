
========================
pibooth-picture-template
========================

|PythonVersions| |PypiPackage| |Downloads|

``pibooth-picture-template`` is a plugin for the `pibooth`_ application.

It permits to define the captures/texts positions and sizes using a template. The template file
(XML based on `mxGraphModel definition <https://jgraph.github.io/mxgraph/docs/tutorial.html>`_)
can be easily created/edited using the free online diagram software `Flowchart Maker`_.


.. image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/FlowchartMaker.png?raw=true
   :align: center
   :width: 500
   :alt: Flowchart Maker
   :target: https://app.diagrams.net


A set of templates can be found on `GitHub <https://github.com/pibooth/pibooth-picture-template/tree/master/templates>`_.

The `fancy.xml <https://github.com/pibooth/pibooth-picture-template/blob/master/templates/fancy.xml?raw=true>`_
template is automatically installed by this plugin in ``~/.config/pibooth/picture_template.xml``.

Below are the pictures generated with this one (learn here how to `Create a template`_):

+---------------------------------------+---------------------------------------+
|          |fancy1_landscape|           |          |fancy3_landscape|           |
+---------------------------------------+---------------------------------------+
|          |fancy2_landscape|           |          |fancy4_landscape|           |
+-------------------+-------------------+-------------------+-------------------+

+-------------------+-------------------+-------------------+-------------------+
| |fancy1_portrait| | |fancy2_portrait| | |fancy3_portrait| | |fancy4_portrait| |
+-------------------+-------------------+-------------------+-------------------+

Install
-------

::

    $ pip3 install pibooth-picture-template

Configuration
-------------

Here below the new configuration options available in the `pibooth`_ configuration.
**The keys and their default values are automatically added to your configuration after first** `pibooth`_ **restart.**

.. code-block:: ini

    [PICTURE]

    # Pictures template path, it should contain 8 pages (4 capture numbers and 2 orientations)
    template = picture_template.xml

.. note:: Edit the configuration by running the command ``pibooth --config``.

Picture orientation
-------------------

A ``TemplateParserError`` is raised if the requested orientation for the selected
captures number can not be found in the template file.

If ``[PICTURE][orientation] = auto`` the best orientation is chosen following these
rules:

* find a template with the correct number of captures and placeholders with same orientation
  than the captures.
* find a template with the correct number of captures.
* find a template with portrait orientation

Create a template
-----------------

The steps below will show how to create a basic template file from scratch using
the `Flowchart Maker`_ application.

This file may contain several templates to define the picture layout for ``1`` /
``2`` / ``3`` / ``4`` captures and ``portrait`` / ``landscape`` orientations.

Step 1: create a new file
^^^^^^^^^^^^^^^^^^^^^^^^^

===========  ==================================================================
 |step1_1|   Click on ``Create New Diagram``.

 |step1_2|   Choose a blank diagram. Modify the name of the diagram, it will be
             the name of the exported file. Click on ``Create``.

 |step1_3|   Select the appropriated paper size. A custom one can be defined in
             *inches*.
===========  ==================================================================

.. note:: It could be easier to start from an existing file. Click on ``Open Existing Diagram``
          to load the default template file located in ``~/.config/pibooth/picture_template.xml``

Step 2: placeholder for captures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

===========  ==================================================================
 |step2_1|   Choose a rectangle to define a capture placeholder. Other shapes
             have no effect and will be considered as rectangles.

 |step2_2|   Resize the rectangle to fit the desired size. The rectangle can
             overflow the border of the page to make design effects. Up to 4
             rectangles can be drawn.

 |step2_3|   The captures placeholders shall be numbered (``1`` to ``4``) to
             define the captures to be placed inside. Colored shapes give a
             better overview of the layout but they are not rendered on the
             final picture.
===========  ==================================================================

.. note:: Images can also be inserted in the template. Use the option ``To back``
          or ``To Front`` to chose the displayed order (PNG and JPG format accepted).

Step 3: placeholder for texts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

===========  ==================================================================
 |step3_1|   Choose a text box to represent a text placeholder.

 |step3_2|   Resize the text box to fit the desired size. Up to 2 text boxes
             can be drawn depending on the  `pibooth`_ configuration.

 |step2_3|   The text placeholders shall be numbered (``1``, ``2``,
             ``footer_text1`` or ``footer_text2``) to define the text to be
             placed inside.
===========  ==================================================================

Step 4: picture resolution
^^^^^^^^^^^^^^^^^^^^^^^^^^

===========  ==================================================================
 |step4_1|   Extra properties can be set to the template. Click on the button
             ``Edit Data`` (close to the paper size settings). Type ``dpi`` in
             the entry box and click on ``Add Property``.

 |step4_2|   By default a resolution of ``600`` DPI is used. It means that the
             picture size will be 2400x3600 pixels for a resolution of 4x6
             inches. Set it to the desired value and click on ``Apply``.
===========  ==================================================================

Step 5: add new a template
^^^^^^^^^^^^^^^^^^^^^^^^^^^

===========  ==================================================================
 |step5_1|   Once the template is created. A new one can be defined for an
             other captures number or other orientation. Click on ``+`` to add
             a new page.

|step5_2|    The same picture can be used several times in the template to
             allows a symmetric template for example (one copy for you, one for
             your guests).
===========  ==================================================================

Step 6: save the template file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

===========  ==================================================================
 |step6_1|   Generate the XML file by clicking ``File``, ``Export as``,
             ``XML...``.

 |step6_2|   Click on ``Export`` (unselect ``Compressed`` if you want to edit
             the file manually later).
===========  ==================================================================

.. note:: Instead of running `pibooth`_ each time you want to test the result of
          your template, use the command ``pibooth-regen``. It will regenerate
          the existing pictures present in ``~/Pictures/pibooth`` using the new
          template.


.. --- Links ------------------------------------------------------------------

.. _`pibooth`: https://pypi.org/project/pibooth

.. _`Flowchart Maker`: https://app.diagrams.net

.. |PythonVersions| image:: https://img.shields.io/badge/python-3.6+-red.svg
   :target: https://www.python.org/downloads
   :alt: Python 3.6+

.. |PypiPackage| image:: https://badge.fury.io/py/pibooth-picture-template.svg
   :target: https://pypi.org/project/pibooth-picture-template
   :alt: PyPi package

.. |Downloads| image:: https://img.shields.io/pypi/dm/pibooth-picture-template?color=purple
   :target: https://pypi.org/project/pibooth-picture-template
   :alt: PyPi downloads

.. --- Examples ---------------------------------------------------------------

.. |fancy1_landscape| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy1_landscape.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy1_landscape

.. |fancy2_landscape| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy2_landscape.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy2_landscape

.. |fancy3_landscape| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy3_landscape.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy3_landscape

.. |fancy4_landscape| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy4_landscape.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy4_landscape

.. |fancy1_portrait| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy1_portrait.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy1_portrait

.. |fancy2_portrait| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy2_portrait.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy2_portrait

.. |fancy3_portrait| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy3_portrait.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy3_portrait

.. |fancy4_portrait| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/examples/fancy4_portrait.jpg?raw=true
   :width: 90 %
   :align: middle
   :alt: fancy4_portrait

.. --- Tuto -------------------------------------------------------------------

.. |step1_1| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step1_1_create.png?raw=true
   :width: 80 %
   :alt: step1_1_create

.. |step1_2| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step1_2_blank.png?raw=true
   :width: 80 %
   :alt: step1_2_blank

.. |step1_3| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step1_3_size.png?raw=true
   :width: 80 %
   :alt: step1_3_size

.. |step2_1| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step2_1_rectangle.png?raw=true
   :width: 80 %
   :alt: step2_1_rectangle

.. |step2_2| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step2_2_rectangle_resize.png?raw=true
   :width: 80 %
   :alt: step2_2_rectangle_resize

.. |step2_3| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step2_3_numbering.png?raw=true
   :width: 80 %
   :alt: step2_3_numbering

.. |step3_1| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step3_1_text.png?raw=true
   :width: 80 %
   :alt: step3_1_text

.. |step3_2| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step3_2_text_resize.png?raw=true
   :width: 80 %
   :alt: step3_2_text_resize

.. |step4_1| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step4_1_property.png?raw=true
   :width: 80 %
   :alt: step4_1_property

.. |step4_2| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step4_2_dpi.png?raw=true
   :width: 80 %
   :alt: step4_2_dpi

.. |step5_1| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step5_1_new_template.png?raw=true
   :width: 80 %
   :alt: step5_1_new_template

.. |step5_2| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step5_2_symetric.jpg?raw=true
   :width: 80 %
   :alt: step5_2_symetric

.. |step6_1| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step6_1_xml.png?raw=true
   :width: 80 %
   :alt: step6_1_xml

.. |step6_2| image:: https://github.com/pibooth/pibooth-picture-template/blob/master/docs/images/step6_2_export.png?raw=true
   :width: 80 %
   :alt: step6_2_export
