import arcpy
import os, uuid

WEB_MAP_INDEX = 0
OUTPUT_FILE_INDEX = 1
LAYOUT_TEMPLATE_FOLDER_INDEX = 2
LAYOUT_TEMPLATE_INDEX = 3

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Advanced Web Map Export"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [ExportWebMap]

def generateFilename():
    """Use the uuid module to generate a GUID as part of the output name
    This will ensure a unique output name
    @rtype: str
    """
    output = 'WebMap_{}.pdf'.format(str(uuid.uuid1()))
    output = os.path.join(arcpy.env.scratchFolder, output)
    return output

class ExportWebMap(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Export Web Map"
        self.description = "Exports a web map into an image file (e.g., PDF)."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="Web Map as JSON",
            name="Web_Map_as_JSON",
            datatype="String",
            parameterType="Required",
            direction="Input")
        param0.value = "" 
        
        param1 = arcpy.Parameter(
            displayName="Output File",
            name="Output_File",
            datatype="File",
            parameterType="Required",
            direction="Output")
        param1.value = generateFilename()


        param2 = arcpy.Parameter(
             displayName="Layout Template Folder",
             name="Layout_Template_Folder",
             datatype="Folder",
             parameterType="Required",
             direction="Input"
         )
        
        param3 = arcpy.Parameter(
             displayName="Layout Template",
             name="Layout_Template",
             datatype="String",
             parameterType="Required",
             direction="Input")
        param3.filter.type = "ValueList"
        
        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        
        template_folder_param = parameters[2]
        template_param = parameters[3]
        
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
        """The source code of the tool.
        Parameters
        Web_Map_as_JSON
        Output_File
        Layout_Template_Folder
        Layout_Template
        """
        
        
        

        
        # Input WebMap json
        Web_Map_as_JSON = parameters[WEB_MAP_INDEX].valueAsText
        
        if Web_Map_as_JSON:
            templateFolder = parameters[LAYOUT_TEMPLATE_FOLDER_INDEX].valueAsText
            
            # The template location in the server data store
            templateMxd = parameters[LAYOUT_TEMPLATE_INDEX].valueAsText
            templateMxd = os.path.join(templateFolder, "%s.mxd" % templateMxd)
            
            # Throw an error if the template MXD does not exist.
            if not arcpy.Exists(templateMxd):
                arcpy.AddError("Template not found: %s." % templateMxd)
               
            # Convert the WebMap to a map document
            result = arcpy.mapping.ConvertWebMapToMapDocument(Web_Map_as_JSON, templateMxd)
            mxd = result.mapDocument
            
            # Reference the data frame that contains the webmap
            # Note: ConvertWebMapToMapDocument renames the active dataframe in the template_mxd to "Webmap"
            df = arcpy.mapping.ListDataFrames(mxd, 'Webmap')[0]
            
            # Remove the service layer
            # This will just leave the vector layers from the template
            for lyr in arcpy.mapping.ListLayers(mxd, data_frame=df):
                if lyr.isServiceLayer:
                    arcpy.mapping.RemoveLayer(df, lyr)
                    
            ## Use the uuid module to generate a GUID as part of the output name
            ## This will ensure a unique output name
            Output_File = parameters[OUTPUT_FILE_INDEX].valueAsText
            
            # Export the WebMap
            arcpy.mapping.ExportToPDF(mxd, Output_File) 
            
            # Set the output parameter to be the output file of the server job
            arcpy.SetParameterAsText(OUTPUT_FILE_INDEX, Output_File)
            
            # Clean up - delete the map document reference
            filePath = mxd.filePath
            del mxd, result
            os.remove(filePath)
