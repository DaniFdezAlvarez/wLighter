from distutils.core import setup
setup(
  name = 'wlighter',         # How you named your package folder (MyLib)
  packages = ['wlighter'],   # Chose the same as "name"
  version = '1.0',      # Start with a small number and increase it with every change you make
  license='Apache2.0',      
  description = 'library to annotate RDF of ShEx containing wikidata URIs with a readable label',   # Give a short description about your library
  author = 'Daniel Fernandez-Alvarez',                   # Type in your name
  author_email = 'danifdezalvarez@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/DaniFdezAlvarez/wLighter',   # Provide either the link to your github or to your website   CONTINUE DOWN HERE



  download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',    # I explain this later on
  keywords = ['SOME', 'MEANINGFULL', 'KEYWORDS'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'validators',
          'beautifulsoup4',
      ],
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)