#!/usr/bin/python

import itk, sys
itk.auto_progress=True
reader = itk.ImageFileReader.US3.New()
# un peu de nettoyage
median = itk.MedianImageFilter.US3US3.New(reader, Radius=2)
r = median.GetRadius()
r.SetElement(2, 1)
# selectionne le noyau
im30 = itk.BinaryThresholdImageFilter.US3US3.New(median, LowerThreshold=30)
# supprime tous les petits trucs qui traine dans l'image
kernel = itk.BinaryBallStructuringElement.US3(Radius=5)
r = kernel.GetRadius()
r.SetElement(2, 1)
kernel.SetRadius(r)
kernel.CreateStructuringElement()
erode = itk.BinaryErodeImageFilter.US3US3.New(im30, Kernel=kernel)
recons = itk.ReconstructionByDilatationImageFilter.US3US3.New(erode, im30)
connected = itk.ConnectedComponentImageFilter.US3US3.New(recons)
noyaux = itk.RelabelComponentImageFilter.US3US3.New(connected)
# il faut faire une fermeture pour lisser les noyaux
# TODO

# les granules
hconvex = itk.HConvexImageFilter.US3US3(median, Height=50)
bGranules = itk.BinaryThresholdImageFilter.US3US3.New(hconvex, LowerThreshold=1)
selctedHConvex = itk.AndImageFilter.US3US3US3.New(recons, bGranules)
# supprime les elts trop petits
gkernel = itk.BinaryBallStructuringElement.US3(Radius=2)
gr = gkernel.GetRadius()
gr.SetElement(2, 1)
gkernel.SetRadius(gr)
gkernel.CreateStructuringElement()
gerode = itk.BinaryErodeImageFilter.US3US3.New(selctedHConvex, Kernel=gkernel)
# reconstruit l'image sans les trucs trops petits
grecons = itk.ReconstructionByDilatationImageFilter.US3US3.New(gerode, selctedHConvex)
gConnected = itk.ConnectedComponentImageFilter.US3US3.New(grecons)
granules = itk.RelabelComponentImageFilter.US3US3.New(gConnected)

gShape = itk.LabelShapeImageFilter.US3.New(granules)
nShape = itk.LabelShapeImageFilter.US3.New(noyaux)

# reader.SetFileName("Lot3embryon4450ZOOM.tif")
# gShape.Update()
# nShape.Update()

#fin de l'executable
#ci dessous la generation de fichiers resultats
reader.SetFileName(sys.argv[1])

gWriter = itk.ImageFileWriter.US3.New(gShape, FileName=sys.argv[1][:-4]+"-granules.tif")
gWriter.Update()

nWriter = itk.ImageFileWriter.US3.New(nShape, FileName=sys.argv[1][:-4]+"-noyaux.tif")
nWriter.Update()

for i in range(1, nShape.GetNumberOfLabels()) :
	f = file("noyaux.txt", 'a')
	f.write(sys.argv[1]+"\t")
	f.write(str(i)+"\t")
	f.write(str(nShape.GetVolume(i))+"\t")
	for j in range(0, 3) :
		if j != 0 :
			f.write(",")
		f.write(str(nShape.GetCenterOfGravity(i).GetElement(j)))
	f.write("\t")
	f.write("\n")
	f.close()
	
for i in range(1, gShape.GetNumberOfLabels()) :
	f = file("granules.txt", 'a')
	f.write(sys.argv[1]+"\t")
	f.write(str(i)+"\t")
	f.write(str(gShape.GetVolume(i))+"\t")
	for j in range(0, 3) :
		if j != 0 :
			f.write(",")
		f.write(str(gShape.GetCenterOfGravity(i).GetElement(j)))
	f.write("\t")
	f.write("\n")
	f.close()
	
# bgr = itk.BinaryThresholdImageFilter.US3US3.New(grecons, LowerThreshold=1, InsideValue=4)
# a = itk.AddImageFilter.US3US3US3.New(noyaux, bgr)
# v = Viewer(a)
# v.AdaptColorAndOpacity()
# 
# 
# v.SetInput(granules.GetOutput())
# v.AdaptColorAndOpacity()



def GetRange(img) :
  import itk
  comp = itk.MinimumMaximumImageCalculator.US3.New(Image=img)
  comp.Compute()
  return (comp.GetMinimum(), comp.GetMaximum())


class Viewer :
  def __init__(self, filt=None, Input=None, MinOpacity=0.0, MaxOpacity=0.2) :
    import qt
    import vtk
    import itkvtk
    from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    self.__imageType__ = 'US3'
    self.__MinOpacity__ = MinOpacity
    self.__MaxOpacity__ = MaxOpacity
    # every QT app needs an app
    self.__app__ = qt.QApplication(['itkviewer'])
    # create the widget
    self.__widget__ = QVTKRenderWindowInteractor()
    self.__ren__ = vtk.vtkRenderer()
    self.__widget__.GetRenderWindow().AddRenderer(self.__ren__)
    self.__itkvtkConverter__ = None
    self.__volumeMapper__ = vtk.vtkVolumeTextureMapper2D()
    self.__volume__ = vtk.vtkVolume()
    self.__volumeProperty__ = vtk.vtkVolumeProperty()
    self.__volume__.SetMapper(self.__volumeMapper__)
    self.__volume__.SetProperty(self.__volumeProperty__)
    self.__ren__.AddVolume(self.__volume__)
    self.__outline__ = vtk.vtkOutlineFilter()
    self.__outlineMapper__ = vtk.vtkPolyDataMapper()
    self.__outlineMapper__.SetInput(self.__outline__.GetOutput())
    self.__outlineActor__ = vtk.vtkActor()
    self.__outlineActor__.SetMapper(self.__outlineMapper__)
    self.__ren__.AddActor(self.__outlineActor__)
    self.AdaptColorAndOpacity(0, 255)
    if filt :
      self.SetInput(filt.GetOutput())
    if Input :
      self.SetInput(Input)
  def Render(self):
    self.__ren__.Render()
  def GetWidget(self) :
    return self.__widget__
  def GetRenderer(self) :
    return self.__ren__
  def GetConverter(self) :
    return self.__itkvtkConverter__
  def GetVolumeMapper(self) :
    return self.__volumeMapper__
  def GetVolume(self) :
    return self.__volume__
  def GetVolumeProperty(self) :
    return self.__volumeProperty__
  def Show(self) :
    self.__widget__.show()
  def Hide(self) :
    self.__widget__.hide()
  def SetInput(self, img) :
    self.__input__ = img
    if img :
      import itkvtk
      self.__itkvtkConverter__ = itkvtk.ImageToVTKImageFilter[self.__imageType__].New(Input=img)
      self.__volumeMapper__.SetInput(self.__itkvtkConverter__.GetOutput())
      self.__outline__.SetInput(self.__itkvtkConverter__.GetOutput())
    self.Render()
  def GetInput(self):
    return self.__input__
  def AdaptColorAndOpacity(self, minVal=None, maxVal=None):
    if minVal == None or maxVal == None :
      m, M = self.GetRange()
      if minVal == None :
        minVal = m
      if maxVal == None :
        maxVal = M
    self.AdaptOpacity(minVal, maxVal)
    self.AdaptColor(minVal, maxVal)
  def AdaptOpacity(self, minVal=None, maxVal=None) :
    import vtk
    if minVal == None or maxVal == None :
      m, M = self.GetRange()
      if minVal == None :
        minVal = m
      if maxVal == None :
        maxVal = M
    opacityTransferFunction = vtk.vtkPiecewiseFunction()
    opacityTransferFunction.AddPoint(minVal, self.__MinOpacity__)
    opacityTransferFunction.AddPoint(maxVal, self.__MaxOpacity__)
    self.__volumeProperty__.SetScalarOpacity(opacityTransferFunction)
  def AdaptColor(self, minVal=None, maxVal=None):
    import vtk
    if minVal == None or maxVal == None :
      m, M = self.GetRange()
      if minVal == None :
        minVal = m
      if maxVal == None :
        maxVal = M
    colorTransferFunction = vtk.vtkColorTransferFunction()
    colorTransferFunction.AddHSVPoint(minVal, 0.0, 0.0, 0.0)
    colorTransferFunction.AddHSVPoint((maxVal-minVal)*0.25, 0.66, 1.0, 1.0)
    colorTransferFunction.AddHSVPoint((maxVal-minVal)*0.5,  0.44, 1.0, 1.0)
    colorTransferFunction.AddHSVPoint((maxVal-minVal)*0.75, 0.22, 1.0, 1.0)
    colorTransferFunction.AddHSVPoint(maxVal,               0.0,  1.0, 1.0)
    self.__volumeProperty__.SetColor(colorTransferFunction)
    self.Render()
  def GetRange(self) :
    conv = self.GetConverter()
    conv.Update()
    return conv.GetOutput().GetScalarRange()
  def GetMaxOpacity(self) :
    return self.__MaxOpacity__
  def GetMinOpacity(self) :
    return self.__MinOpacity__
  def SetMaxOpacity(self, val) :
    self.__MaxOpacity__ = val
    self.AdaptColorAndOpacity()
  def SetMinOpacity(self, val) :
    self.__MinOpacity__ = val
    self.AdaptColorAndOpacity()
