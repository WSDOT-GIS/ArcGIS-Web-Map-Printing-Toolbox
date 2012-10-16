import arcpy


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "PDF Export"
        self.alias = "pdf"

        # List of tool classes associated with this toolbox
        self.tools = [ExportPdf]


class ExportPdf(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Export PDF"
        self.description = ""
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        import arcpy
        import os
        import uuid
        
        # The template location in the registered folder (as UNC path)
        templatePath = '//MyComputerName/MyDataStore/USA'
        
        # Input WebMap json
        Web_Map_as_JSON = arcpy.GetParameterAsText(0)
        
        # Format for output
        Format = arcpy.GetParameterAsText(1)
        if Format == '#' or not Format:
            Format = "PDF" 
        
        # Input Layout template
        Layout_Template = arcpy.GetParameterAsText(2)
        if Layout_Template == '#' or not Layout_Template:
            Layout_Template = "NorthwesternUSA" 
            
        # Extra parameter - georef_info
        Georef_info = arcpy.GetParameterAsText(3)
        if Georef_info == '#' or not Georef_info:
            Georef_info = "False"
        
        # Convert Georef_info string to boolean
        if Georef_info.lower() == 'false': 
            Georef_info_bol = False
        elif Georef_info.lower() == 'true': 
            Georef_info_bol = True
        
        # Get the requested map document
        templateMxd = os.path.join(templatePath, Layout_Template + '.mxd')
        
        # Convert the WebMap to a map document
        result = arcpy.mapping.ConvertWebMapToMapDocument(Web_Map_as_JSON, templateMxd)
        mxd = result.mapDocument
        
        # Reference the data frame that contains the webmap
        # Note: ConvertWebMapToMapDocument renames the active dataframe in the template_mxd to "Webmap"
        df = arcpy.mapping.ListDataFrames(mxd, 'Webmap')[0]
        
        # Get a list of all service layer names in the map
        serviceLayersNames = [slyr.name for slyr in arcpy.mapping.ListLayers(mxd, data_frame=df) 
                              if slyr.isServiceLayer and slyr.visible and not slyr.isGroupLayer]
        
        # Create a list of all possible vector layer names in the map that could have a 
        # corresponding service layer
        vectorLayersNames = [vlyr.name for vlyr in arcpy.mapping.ListLayers(mxd, data_frame=df) 
                             if not vlyr.isServiceLayer and not vlyr.isGroupLayer]
        
        # Get a list of all vector layers that don't have a corresponding service layer
        removeLayerNameList = [vlyrName for vlyrName in vectorLayersNames 
                               if vlyrName not in serviceLayersNames]
        
        # Remove all vector layers that don't have a corresponding service layer
        for lyr in arcpy.mapping.ListLayers(mxd, data_frame=df):
            if not lyr.isGroupLayer \
            and not lyr.isServiceLayer \
            and lyr.name in removeLayerNameList \
            and lyr.name in vectorLayersNames:
                arcpy.mapping.RemoveLayer(df, lyr)
                        
        # Reference the legend in the map document
        legend = arcpy.mapping.ListLayoutElements(mxd, "LEGEND_ELEMENT")[0]
        
        # Get a list of service layers that are on in the legend because the incoming 
        # JSON can specify which service layers/sublayers are on/off in the legend
        legendServiceLayerNames = [lslyr.name for lslyr in legend.listLegendItemLayers() 
                                   if lslyr.isServiceLayer and not lslyr.isGroupLayer]
        
        # Remove vector layers from the legend where the corresponding service layer 
        # is also off in the legend
        for lvlyr in legend.listLegendItemLayers():
            if not lvlyr.isServiceLayer \
            and lvlyr.name not in legendServiceLayerNames \
            and not lvlyr.isGroupLayer \
            and lvlyr.name in vectorLayersNames:
                legend.removeItem(lvlyr)
        
        # Remove all service layers
        # This will leave only vector layers that had corresponding service layers
        for slyr in arcpy.mapping.ListLayers(mxd, data_frame=df):
            if slyr.isServiceLayer:
                arcpy.mapping.RemoveLayer(df, slyr)
                
        # ConvertWebMapToMapDocument renames the active dataframe in the template_mxd to "Webmap".
        # Lets rename it to something more meaningful.
        df.name = Layout_Template
        
        # Use the uuid module to generate a GUID as part of the output name
        # This will ensure a unique output name
        output = 'WebMap_{}.{}'.format(str(uuid.uuid1()), Format)
        Output_File = os.path.join(arcpy.env.scratchFolder, output)
        
        # Export the WebMap
        if Format.lower() == 'pdf':
            arcpy.mapping.ExportToPDF(mxd, Output_File, georef_info=Georef_info_bol) 
        elif Format.lower() == 'png':
            arcpy.mapping.ExportToPNG(mxd, Output_File)
        
        # Set the output parameter to be the output file of the server job
        arcpy.SetParameterAsText(4, Output_File)
        
        # Clean up - delete the map document reference
        filePath = mxd.filePath
        del mxd, result
        os.remove(filePath)
