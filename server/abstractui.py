#!/usr/bin/env python
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import requests
import time
import datetime
from pprint import pprint
import re,os

"""
Abstract UI methods.
History -
07032013:
"""

def find_workflow():
	"""
	Selection: user_name, time_interval [start_time, end_time], completion_status
	Selection_return: {W_UID, W_composite_ID, name, description, user_name, creation_time, start_time, end_time, completion_status, status_explanation, {CM_UID}}
	"""
	pass

def get_worflow_info():
	"""
	Selection:  W-UID / W_composite_ID
	Selection_return: W_UID, W_composite_ID, name, description, user_name, creation_time, start_time, end_time, completion_status, status_explanation, {CM_UID}

	"""
	pass

def get_workflow_structure():
	"""
	Selection:  W_UID
	Selection_return: W_UID, [{UID, object_name, object-type}, {parent_UID, parent_type, child_UID, child_type}]

	"""
	pass

def find_data_object():
	"""
	Selection:  name, W_composite_ID
	Selection_return: {DO_UID, name, W_UID, W_composite_ID, description, URI_of_data, {CM_UID}}

	"""
	pass

def get_data_object():
	"""
	Selection:  DO_UID
	Selection_return:  DO_UID, name, description, URI_of_data, {CM_UID}

	"""
	pass

def find_activity():
	"""
	Selection:  name, W_composite_ID, completion_status
	Selection_return: {A_GUID, name,  W_UID, W_composite_ID , description, URI_of_executable_file, start_time, end_time, completion_status, status_explanation, {CM_UID}}

	"""
	pass

def get_activity():
	"""
	Selection:  A_UID
	Selection_return: A_GUID, name,  W_UID, W_composite_ID , description, URI_of_executable_file, start_time, end_time, completion_status, status_explanation, {CM_UID}
	"""
	pass

def find_comment():
	"""
	Selection:  text (keyword)
	Selection_return: CM_UID, name, text, URI_of_comment, comment_type, target_UID, target_type, {next level CM_UID}

	"""
	pass

def get_comment():
	"""
	Selection:  CM_UID
	Selection_return: CM_UID, name, text, URI_of_comment, comment_type, target_UID, target_type

	"""
	pass

def abstractui_test():
	"""
	unit tests for all methods
	"""
	print "unit tests...."

if __name__ == '__main__':
	abstractui_test()	

