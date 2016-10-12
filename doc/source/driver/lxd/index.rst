LXD
===

The LXD driver uses `lxd <https://github.com/lxc/lxd>`_ containers.

Only local LXD servers accessible over a unix domain socket are supported. LXD
remotes cannot be used to launch containers, however a remote can be used for
container images.

Requirements
------------

On the LXD host both `lxd <https://github.com/lxc/lxd>`_ and the python module
`pylxd <https://github.com/lxc/pylxd>`_ are required.

Containers will need ``python`` installed either as part of the image or as
part of ``playbook.yml`` using the ``ansible`` `raw
module<http://docs.ansible.com/ansible/raw_module.html>`_.

Usage
-----

Configuration for each container is passed directly to ``pylxd``. Any
configurarion options available in the `pylxd api
<https://github.com/lxc/lxd/blob/master/doc/rest-api.md#10containers>`_ can be
used.

A minimal container definition requires:

* ``name`` - name of the LXD container
* ``source`` - details of the container image

The ``source`` dictionary requires:

* ``type`` - this should be set to ``image``

And either:

* ``fingerprint`` - SHA-256 of the image

or:

* ``alias`` - user friendly name for the image


A simple ``lxd`` section in ``molecule.yml``:

.. code-block:: yaml

  lxd:
    containers:
      - name: foo
        source:
          type: image
          fingerprint: b95710f4d445
      - name: bar
        source:
          type: image
          alias: ubuntu/devel

Using more LXD api options:

.. code-block:: yaml

  lxd:
    containers:
      - name: foo
        architecture: x86_64
        config:
          limits.cpu: "2"
        profile: ["default"]
        source:
          type: image
          mode: pull
          server: "https://10.0.2.3:8443"
          alias: ubuntu/devel
