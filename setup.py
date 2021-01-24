from distutils.core import setup
setup(
  name = 'wlighter',
  packages = ['wlighter'],
  version = '1.0.1', 
  license='Apache2.0',      
  description = 'library to annotate RDF of ShEx containing wikidata URIs with a readable label', 
  author = 'Daniel Fernandez-Alvarez',        
  author_email = 'danifdezalvarez@gmail.com',    
  url = 'https://github.com/DaniFdezAlvarez/wLighter', 
  download_url = 'https://github.com/DaniFdezAlvarez/wLighter/archive/1.0.1.tar.gz',  
  keywords = ['wikidata', 'annotation', 'properties', 'entities', 'rdf', 'shex'],   
  install_requires=[         
          'requests'
      ],
  classifiers=[
    'Development Status :: 4 - Beta',     
    'Intended Audience :: Developers',      
    'Programming Language :: Python :: 3'     
  ],
)