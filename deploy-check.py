# Copyright (c) 2013, Diogo Kollross
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
# 
# Redistributions of source code must retain the above copyright notice, this list
# of conditions and the following disclaimer. Redistributions in binary form must
# reproduce the above copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided with the
# distribution. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
# OF SUCH DAMAGE.


def join_script_path(path):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


import os.path
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

sys.path.append(join_script_path('bcel-5.2.jar'))

from java.io import ByteArrayInputStream
from java.util import Properties
from javax.xml.parsers import DocumentBuilderFactory
from javax.xml.parsers import DocumentBuilder
from org.apache.bcel.classfile import ClassParser
from org.apache.bcel.classfile import JavaClass
from org.w3c.dom import Document
from javax.xml.xpath import XPathConstants
from javax.xml.xpath import XPathFactory


# Pre-defined functions
def fail(message):
    raise AssertionError(message)


deploy_files_data = {}
def get_file_data(filename):
    if filename not in deploy_files_data:
        data = deploy_parent_files[filename].read(deploy_original_filenames[filename])
        deploy_files_data[filename] = data
    return deploy_files_data[filename]


deploy_files_properties = {}
def get_file_properties(filename):
    if filename not in deploy_files_properties:
        data = get_file_data(filename)
        input_stream = ByteArrayInputStream(data)
        properties = Properties()
        properties.load(input_stream)
        
        deploy_files_properties[filename] = properties
    return deploy_files_properties[filename]

    
deploy_files_element_trees = {}
def get_file_element_tree(filename):
    if filename not in deploy_files_element_trees:
        data = get_file_data(filename)
        input_stream = ByteArrayInputStream(data)
        
        db_factory = DocumentBuilderFactory.newInstance()
        db = db_factory.newDocumentBuilder()
        element_tree = db.parse(input_stream)
        element_tree.getDocumentElement().normalize()
        
        deploy_files_element_trees[filename] = element_tree
    return deploy_files_element_trees[filename]


deploy_files_java_classes = {}
def get_file_java_class(filename):
    if filename not in deploy_files_java_classes:
        data = get_file_data(filename)
        input_stream = ByteArrayInputStream(data)
        parser = ClassParser(input_stream, filename)
        java_class = parser.parse()
        
        deploy_files_java_classes[filename] = java_class
    return deploy_files_java_classes[filename]


def exists(filename):
    return filename in deploy_filenames


def has_text(filename, text):
    return text in get_file_data(filename)


def has_property(filename, name):
    properties = get_file_properties(filename)
    return properties.containsKey(name)


def get_property(filename, name):
    properties = get_file_properties(filename)
    return properties.getProperty(name)


def has_xml(filename, xpath):
    return bool(get_xml(filename, xpath))


def get_xml(filename, xpath):
    element_tree = get_file_element_tree(filename)
    xpath_engine = XPathFactory.newInstance().newXPath()
    node_list = xpath_engine.evaluate(xpath, element_tree, XPathConstants.NODESET)
    nodes = [node_list.item(i) for i in range(node_list.getLength())]

    return nodes


def has_java_constant(filename, value):
    java_class = get_file_java_class(filename)
    constants = java_class.getConstantPool().getConstantPool()
    for constant in constants:
        if constant is None:
            continue
        
        constant_value = None
        try:
            constant_value = constant.getBytes()
        except:
            pass
        
        if constant_value is not None and constant_value == value:
            return True
    return False


# Get arguments
if len(sys.argv) != 3:
    print 'Usage: deploy-check PROFILE_1[,PROFILE_2...] DEPLOY'
    print 'Verifies the content of a JavaEE deploy file'
    sys.exit(1)

profiles = sys.argv[1].split(',')
deploy_filename = sys.argv[2]


# Open deploy
deploy_filenames = []
deploy_parent_files = {}
deploy_original_filenames = {}
def open_deploy(file_or_name, parent_path = ''):
    deploy_file = zipfile.ZipFile(file_or_name, 'r')
    for member_name in deploy_file.namelist():
        member_path = parent_path + '/' + member_name
        deploy_filenames.append(member_path)
        deploy_parent_files[member_path] = deploy_file
        deploy_original_filenames[member_path] = member_name
        
        if member_name[-4:].lower() in ('.war', '.jar'):
            member_data = deploy_file.read(member_name)
            member_file = tempfile.TemporaryFile()
            member_file.write(member_data)
            
            open_deploy(member_file, member_path)


open_deploy(deploy_filename)


# Run profiles
try:
    for profile_name in profiles:
        profile_filename = join_script_path(profile_name + '.py')
        profile_code = file(profile_filename, 'r').read()
        exec(profile_code)
    
    print 'Deploy is OK'
except AssertionError, e:
    print 'FAILED: %s' % (e.message)

