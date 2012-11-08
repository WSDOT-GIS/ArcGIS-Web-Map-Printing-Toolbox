import arcpy
import os, uuid, re

class Toolbox(object):
	def __init__(self):
		"""Define the toolbox (the name of the toolbox is the name of the
		.pyt file)."""
		self.label = "PDF Export"
		self.alias = "pdf"
		# List of tool classes associated with this toolbox
		self.tools = [ExportPdf]

def generateFilename(ext=".pdf"):
	"""Use the uuid module to generate a GUID as part of the output name
	This will ensure a unique output name
	@rtype: str
	"""
	output = 'WebMap_%s%s' % (str(uuid.uuid1()), ext)
	output = os.path.join(arcpy.env.scratchFolder, output)
	return output
		
class ExportPdf(object):
	_WEB_MAP_AS_JSON_INDEX = 0
	_FORMAT_INDEX = 1
	_OUTPUT_FILE_INDEX = 2
	_TEMPLATE_FOLDER_INDEX = 3
	_LAYOUT_TEMPLATE_INDEX = 4
	_RESOLUTION_PARAM_INDEX = 5
	
	def __init__(self):
		"""Define the tool (tool name is the name of the class)."""
		self.label = "Export PDF"
		self.description = "Export to PDF"
		self.canRunInBackground = False
		
	def getParameterInfo(self):
		"""Define parameter definitions"""
		"""Define parameter definitions"""
		webMapParam = arcpy.Parameter(
			displayName="Web Map as JSON",
			name="Web_Map_as_JSON",
			datatype="String",
			parameterType="Optional",
			direction="Input")
		webMapParam.value = "" 
		
		formatParam = arcpy.Parameter(
			displayName="Format",
			name="Format",
			datatype="String",
			parameterType="Required",
			direction="Input")
		formatParam.filter.type = "ValueList"
		formatParam.filter.list = ["PDF"]
		formatParam.value = "PDF"
		
		outputFileParam = arcpy.Parameter(
			displayName="Output File",
			name="Output_File",
			datatype="File",
			parameterType="Required",
			direction="Output")
		outputFileParam.value = generateFilename()
		
		templateFolderParam = arcpy.Parameter(
			displayName="Layout Template Folder",
			name="Layout_Template_Folder",
			datatype="Folder",
			parameterType="Required",
			direction="Input")
		
		templateParam = arcpy.Parameter(
				displayName="Layout Template",
				name="Layout_Template",
				datatype="String",
				parameterType="Required",
				direction="Input")
		templateParam.filter.type = "ValueList"
		
		resolutionParam = arcpy.Parameter(
				displayName="Resolution",
				name="Resolution",
				datatype="Long",
				parameterType="Optional",
				direction="Input")
		resolutionParam.filter.type = "Range"
		resolutionParam.filter.list = [96, 300]
		
		params = [webMapParam, formatParam, outputFileParam, 
				templateFolderParam, templateParam, resolutionParam]
		
		return params
	
	def isLicensed(self):
		"""Set whether tool is licensed to execute."""
		return True
	
	def updateParameters(self, parameters):
		"""Modify the values and properties of parameters before internal
		validation is performed.  This method is called whenever a parameter
		has been changed."""
		template_folder_param = parameters[self._TEMPLATE_FOLDER_INDEX]
		template_param = parameters[self._LAYOUT_TEMPLATE_INDEX]
		
		if template_folder_param.altered and not template_folder_param.hasBeenValidated:
			templates = []
			template_folder = template_folder_param.valueAsText
			# Clear the existing items in the filter list.
			if os.path.exists(template_folder):
				for f in os.listdir(template_folder):
					name, ext = os.path.splitext(f)
					if ext == ".mxd":
						#template_param.filter.list.append(name)
						templates.append(name)
			template_param.filter.list = templates
	
	def updateMessages(self, parameters):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		return
	
	def execute(self, parameters, messages):
		"""The source code of the tool."""
		# based on sample from http://resources.arcgis.com/en/help/main/10.1/#/Tutorial_Advanced_high_quality_web_map_printing_exporting_using_arcpy_mapping/0154000005z2000000/
		# The template location in the registered folder (as UNC path)
		
		# Input WebMap json
		Web_Map_as_JSON = parameters[self._WEB_MAP_AS_JSON_INDEX].valueAsText
		
		if Web_Map_as_JSON:
			templatePath = parameters[self._TEMPLATE_FOLDER_INDEX].valueAsText
				# Format for output
			Format = parameters[self._FORMAT_INDEX].valueAsText
			if Format == '#' or not Format:
				Format = "PDF"

			# Input Layout template
			Layout_Template = parameters[self._LAYOUT_TEMPLATE_INDEX].valueAsText
	
			# Get the requested map document
			templateMxd = os.path.join(templatePath, Layout_Template + '.mxd')
			
			# Convert the WebMap to a map document
			result = arcpy.mapping.ConvertWebMapToMapDocument(Web_Map_as_JSON, templateMxd)
			mxd = result.mapDocument
			
			try:
				# Reference the data frame that contains the webmap
				# Note: ConvertWebMapToMapDocument renames the active dataframe in the template_mxd to "Webmap"
				df = arcpy.mapping.ListDataFrames(mxd, 'Webmap')[0]
				
				# Use the uuid module to generate a GUID as part of the output name
				# This will ensure a unique output name
				Output_File = parameters[self._OUTPUT_FILE_INDEX].valueAsText
				resolution = parameters[self._RESOLUTION_PARAM_INDEX].value
				
				if resolution <= 0:
					resolution = None
				
				# Export the WebMap
				if re.match("PDF", Format, re.IGNORECASE):
					arcpy.mapping.ExportToPDF(mxd, Output_File, resolution=resolution, georef_info=True) 
				elif re.match("PNG", Format, re.IGNORECASE):
					arcpy.mapping.ExportToPNG(mxd, Output_File)
		
				# Set the output parameter to be the output file of the server job
				arcpy.SetParameterAsText(4, Output_File)
			finally:
				# Clean up - delete the map document reference
				filePath = mxd.filePath
				del mxd, result
				os.remove(filePath)
