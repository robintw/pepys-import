==================================
Contributing to the Documentation
==================================


The source for Pepys Import documentation is in this directory. Our
documentation uses
`Sphinx <https://www.sphinx-doc.org/en/master/index.html>`_ and
`Sphinx's RTD Theme <https://sphinx-rtd-theme.readthedocs.io/en/stable/>`_.

Building the documentation
--------------------------

* Install requirements.txt in the top level of the
  project: :code:`pip install -r requirements.txt` .
* From the top level directory, :code:`cd` into the
  :code:`docs/` folder and run: :code:`make html`

If you would like regenerate the document structure:

- :code:`sphinx-quickstart` `(sphinx-quickstart documentation) <https://www.sphinx-doc.org/en/master/usage/quickstart.html#setting-up-the-documentation-sources>`_ can be called to set up a source directory and create necessary configurations.
- Another option is using the following code: :code:`sphinx-apidoc -F -o docs pepys_import` `(sphinx-apidoc documentation) <https://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html>`_

After it's done, you can run :code:`make html` in :code:`docs/` folder.
