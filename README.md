deploy-check
================================

deploy-check is a script in Jython (Python for Java) that verifies the contents of a JavaEE deploy file or any other ZIP that contains text files, properties files, XML files or Java class files.

Usage
-------------------------

The command line usage is:

    java -jar jython-standalone-2.5.3.jar deploy-check.py PROFILE_1[,PROFILE_2...] DEPLOY

Where PROFILE_1,PROFILE_2 is a comma delimited list of names of profiles that are checked in sequence until one of them fails or all succeed. A profile is a Python script that is executed to check the contents of the DEPLOY file. All profile scripts must be in the same directory of deploy-check.py.

DEPLOY is any ZIP (eg: JAR, WAR, EAR) file.

The following functions are available inside profile scripts:

* `exists(filename)`: returns True if the 'filename' file exists in the deploy
* `has_text(filename, text)`: returns True if 'text' exists in the 'filename' file
* `has_property(filename, name)`: returns True if the 'filename' file is a properties file with the 'name' property
* `get_property(filename, name)`: returns the value of the 'name' property in the 'filename' properties file
* `has_xml(filename, xpath)`: return True if the 'filename' file is a XML file and matches the 'xpath' expression
* `get_xml(filename, xpath)`: returns all nodes (as a list of `org.w3c.dom.Node` objects) of the XML file 'filename' that match the 'xpath' expression
* `has_java_constant(filename, value)`: returns True if 'filename' is a Java class file that contains the 'value' String constant

You can signal the failure in a test by raising `AssertionError`.

```python
# Checks some WAR deploy meant to be used in production
assert exists('/web.xml'), 'web.xml does not exist'
assert get_property('/struts.properties', 'struts.devMode') == 'false', 'Struts is not configured to production mode'
assert has_xml('/web.xml', './/servlet-class[text() = "mysite.server.MyServlet"]'), 'Wrong servlet class configured in web.xml'
assert has_java_constant('/WEB-INF/classes/mysite/Constants.class', 'my-development-server'), 'mysite.Constants not configured to production mode'
```

All paths are relative to the original DEPLOY file and start with a slash. You can refer to files inside ZIP files (eg: WAR files) as they were directories.

    /META-INF/persistence.xml
    /ViewController.war/WEB-INF/web.xml

Requirements
-------------------------

* Jython 2.5.3 (http://www.jython.org/)
* Commons BCEL (http://commons.apache.org/proper/commons-bcel/)
