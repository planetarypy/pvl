============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs or Ask for Features via Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We want to hear from you!  You can report bugs, ask for new features,
or just raise issues or concerns via logging an `Issue via our
GitHub repo <https://github.com/planetarypy/pvl/issues>`_.


Fix Bugs or Implement Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Look through the GitHub Issues for bugs to fix or feautures to implement.
If anything looks tractable to you, work on it.  Most (if not all) PRs should
be based on an Issue, so if you're thinking about doing some coding on a topic
that isn't covered in an Issue, please author one so you can get some feedback
while you work on your PR.

Write Documentation
~~~~~~~~~~~~~~~~~~~

pvl could always use more documentation, whether as part of the
official pvl docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an `Issue
<https://github.com/planetarypy/pvl/issues>`_.


Get Started!
------------

Ready to contribute? Here's how to set up `pvl` for local development.

1. Fork the `pvl` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/pvl.git

3. Install your local copy into a virtual environment like virtualenv
   or conda. Assuming you have virtualenvwrapper installed, this is
   how you set up your fork for local development::

    $ mkvirtualenv pvl
    $ cd pvl/
    $ pip install -r requirements.txt

   If you are a conda user::

    $ cd pvl/
    $ conda env create -n pvldev -f environment.yml
    $ conda activate pvldev
    $ pip install --no-deps -e .

   The last `pip install` installs pvl in "editable" mode which facilitates
   testing.

4. Create a branch for local 
   development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the tests,
   including testing other Python versions with tox::

    $ make lint
    $ make test
    $ make test-all

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a `pull request <https://github.com/planetarypy/pvl/pulls>`_.


Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in HISTORY.rst and potentially update the README.rst 
   or other documentation files.
3. The pull request should work for Python 3.6, 3.7, and 3.8. Check
   https://travis-ci.org/github/planetarypy/pvl
   and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

	$ pytest tests/test_pvl.py


What to expect
--------------

We want to keep development moving forward, and you should expect
activity on your PR within a week or so.


Rules for Merging Pull Requests
-------------------------------

Any change to resources in this repository must be through pull
requests (PRs). This applies to all changes to documentation, code,
binary files, etc. Even long term committers must use pull requests.

In general, the submitter of a PR is responsible for making changes
to the PR. Any changes to the PR can be suggested by others in the
PR thread (or via PRs to the PR), but changes to the primary PR
should be made by the PR author (unless they indicate otherwise in
their comments). In order to merge a PR, it must satisfy these conditions:

1. Have been open for 24 hours.
2. Have one approval.
3. If the PR has been open for 1 week without approval or comment, then it
   may be merged without any approvals.

Pull requests should sit for at least 24 hours to ensure that
contributors in other timezones have time to review. Consideration
should also be given to weekends and other holiday periods to ensure
active committers all have reasonable time to become involved in
the discussion and review process if they wish.

In order to encourage involvement and review, we encourage at least
one explicit approval from committers that are not the PR author.

However, in order to keep development moving along with our low number of
active contributors, if a PR has been open for a week without comment, then
it could be committed without an approval.

The default for each contribution is that it is accepted once no
committer has an objection, and the above requirements are
satisfied. 

In the case of an objection being raised in a pull request by another
committer, all involved committers should seek to arrive at a
consensus by way of addressing concerns being expressed by discussion,
compromise on the proposed change, or withdrawal of the proposed
change.

If a contribution is controversial and committers cannot agree about
how to get it merged or if it should merge, then the developers
will escalate the matter to the PlanetaryPy TC for guidance.  It
is expected that only a small minority of issues be brought to the
PlanetaryPy TC for resolution and that discussion and compromise
among committers be the default resolution mechanism.

Exceptions to the above are minor typo fixes or cosmetic changes
that don't alter the meaning of a document. Those edits can be made
via a PR and the requirement for being open 24 h is waived in this
case.


PVL People
----------

- A PVL **Contributor** is any individual creating or commenting
  on an issue or pull request.  Anyone who has authored a PR that was
  merged should be listed in the AUTHORS.rst file.  

- A PVL **Committer** is a subset of contributors who have been
  given write access to the repository.

All contributors who get a non-trivial contribution merged can
become Committers.  Individuals who wish to be considered for
commit-access may create an Issue or contact an existing Committer
directly.

Committers are expected to follow this policy and continue to send
pull requests, go through proper review, etc.


Workflow and Deploying
----------------------

The workflow concept we use in the pvl project is as follows.
If you are familiar with Git workflows, it is mostly based on a
Gitflow model, but there is not a separate *develop* branch from
the *main* branch (at the moment, we don't need that much formalism),
so *main* is the development branch.

The pvl library follows the `Semantic Versioning 2.0.0
specification <https://semver.org>`_, such that released pvl
version numbers follow this pattern: ``{major}.{minor}.{patch}``.

In this section, as a shorthand for ``{major}.{minor}.{patch}``,
we will use *a.b.c*, but all actual versions in the repo will be
numeric.  When we talk about version *a.b.c*, consider those letters
as immutable variables that hold integers, and ``a += 1 == b, c +=
1 == d``, etc.  So *a.b.c* is some starting state, which could
represent *1.2.3*, then *a.b.d* would be *1.2.4* or *a.c.0* would
be *1.3.0*, etc.

Here is an example workflow :

+------------------------------------------------+--------+-------+-----------+
| Bugfix Workflow                                | Branch | Tests | Version   |
+================================================+========+=======+===========+
| After the commit that releases a.b.c to main   | main   | pass  | a.b.c     |
| it should have been tagged va.b.c              |        |       |           |
+------------------------------------------------+--------+-------+-----------+
| **A software bug is discovered.**                                           |
+------------------------------------------------+--------+-------+-----------+
| Make a *hotfix* branch (could be an external   | hotfix |       |           |
| PR branch)                                     |        |       |           |
+------------------------------------------------+        +-------+           |
| First commit should be the 'failing tests'     |        | fail  |           |
| commit. Craft tests to verify the failure      |        |       |           |
| mode and commit the tests, without touching    |        |       |           |
| the main code.  This allows others to see      |        |       |           |
| exactly what the problems are.                 |        |       |           |
+------------------------------------------------+        |       |           |
| Make commits on *hotfix* to address issue      |        |       |           |
+------------------------------------------------+        +-------+           |
| Once tests pass, make a final commit, and it   |        | pass  |           |
| is ready for merging!                          |        |       |           |
+------------------------------------------------+--------+-------+-----------+
| External developers can now issue a pull request to get this merged into    |
| master.                                                                     |
|                                                                             |
| What follows is what internal developers do when a PR is received:          |
+------------------------------------------------+--------+-------+-----------+
| Checkout the proposed *hotfix* branch and      | hotfix |       |           |
| verify:                                        |        |       |           |
|                                                |        |       |           |
| 1. Are there tests that exercise the bug?      |        |       |           |
| 2. Does ``make lint`` pass?                    |        |       |           |
| 3. Does ``make test`` pass?                    |        |       |           |
| 4. Does ``make test-all`` pass?                |        |       |           |
| 5. Is it based on master?                      |        |       |           |
|                                                |        |       |           |
| Iterate with the submitter, if needed.         |        |       |           |
+------------------------------------------------+--------+-------+-----------+
| When satisfied with the above (no pushing until after the tag step):        |
+------------------------------------------------+--------+-------+-----------+
| Starting state: ``git checkout master``        | main   | pass  | a.b.c     |
+------------------------------------------------+--------+       |           |
| ``git branch hotfix``                          | hotfix |       |           |
|                                                |        |       |           |
| Checkout hotfix, may need to                   |        |       |           |
| ``git rebase master`` if master has advanced.  |        |       |           |
+------------------------------------------------+        |       +-----------+
| Commit with bump2version::                     |        |       | a.b.d-dev |
|                                                |        |       |           |
|   bump2version patch                           |        |       |           |
+------------------------------------------------+        +-------+           |
| Is there a suitable first `failing-tests`      |        | fail  |           |
| commit?  If not, decide how important it is.   |        | in    |           |
| If it is important to have those failing tests |        | the   |           |
| as the first item in the commit history, then  |        | first |           |
| you'll have to do some commit surgery with     |        | commit|           |
| ``git rebase -i`` and other things to arrange  |        |       |           |
| that.                                          |        |       |           |
+------------------------------------------------+        +-------+           |
| * If there are any new external developers:    |        | pass  |           |
|   add to ``AUTHORS.rst`` (if they haven't)     |        |       |           |
| * Edit ``HISTORY.rst`` to describe what        |        |       |           |
|   happened by reviewing commit messages.       |        |       |           |
| * If there are any commits in master since     |        |       |           |
|   the last release, include them in the        |        |       |           |
|   ``HISTORY.rst`` file, too.                   |        |       |           |
| * Otherwise check that everything is ready     |        |       |           |
|   to be merged back into master, and perform   |        |       |           |
|   a final pre-bump commit.                     |        |       |           |
+------------------------------------------------+        |       |           |
| Tidy commits with ``git rebase -i master``     |        |       |           |
| so that the commit history looks like this     |        |       |           |
| (most recent last):                            |        |       |           |
|                                                |        |       |           |
| #. Found a bug, these tests show what's wrong  |        |       |           |
| #. Bump version: a.b.c → a.b.d-dev             |        |       |           |
| #. Fixed the bug by doing x, y, and z          |        |       |           |
|                                                |        |       |           |
| Additional commits are fine, but any final     |        |       |           |
| ``HISTORY.rst`` or ``AUTHORS.rst`` changes     |        |       |           |
| should probably be squashed into the last      |        |       |           |
| commit.                                        |        |       |           |
+------------------------------------------------+        |       +-----------+
| This wraps up this branch and readies it for   |        |       | a.b.d     |
| merging with master::                          |        |       |           |
|                                                |        |       |           |
|  bump2version release --tag                    |        |       |           |
|     --tag-message                              |        |       |           |
|     'something descriptive'                    |        |       |           |
+------------------------------------------------+--------+       |           |
| apply to master::                              | main   |       |           |
|                                                |        |       |           |
|   git checkout master                          |        |       |           |
|   git merge hotfix                             |        |       |           |
+------------------------------------------------+        |       |           |
| ::                                             |        |       |           |
|                                                |        |       |           |
|  git push                                      |        |       |           |
|  git push --tags                               |        |       |           |
+------------------------------------------------+--------+-------+-----------+
| The topic branch can now be deleted::                                       |
|                                                                             |
|   git branch -d hotfix                                                      |
+-----------------------------------------------------------------------------+
| Go to GitHub repo, ensure that all tests passed.                            |
|                                                                             |
| If so, go to "Releases" and "Draft New Release"                             |
|                                                                             |
| Give the most recent HISTORY.rst entry as the "description" of the Release. |
|                                                                             |
| This should then trigger the upload to PyPI workflow.                       |
+-----------------------------------------------------------------------------+
| Once PyPI updates, conda-forge should notice and auto-PR an update.         |
+-----------------------------------------------------------------------------+
 
