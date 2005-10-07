#!/usr/bin/python

import itk, sys
itk.auto_progress=True
reader = itk.ImageFileReader.US3.New()
# spacing is wrong... let's fix it
spacing = itk.Vector.D3()
spacing.Fill(1)
spacing[2] = 3
changeInfo = itk.ChangeInformationImageFilter.US3.New(reader, OutputSpacing=spacing, ChangeSpacing=True)
# resample image to be isotropic
resample = itk.IsotropicResolutionImageFilter.US3US3.New(changeInfo, MaximumIncrease=2)

# un peu de nettoyage
median = itk.MedianImageFilter.US3US3.New(resample, Radius=2)
# r = median.GetRadius()
# r.SetElement(2, 1)

# selectionne le noyau
nThreshold = itk.BinaryThresholdImageFilter.US3US3.New(median, LowerThreshold=30)
# supprime tous les petits trucs qui trainent dans l'image
kernel = itk.BinaryBallStructuringElement.US3(Radius=5)
r = kernel.GetRadius()
# r.SetElement(2, 1)
kernel.SetRadius(r)
kernel.CreateStructuringElement()
nOpen = itk.OpeningByReconstructionImageFilter.US3US3.New(nThreshold, Kernel=kernel)
nConnected = itk.ConnectedComponentImageFilter.US3US3.New(nOpen)
noyaux = itk.RelabelComponentImageFilter.US3US3.New(nConnected)
# il faut faire une fermeture pour lisser les noyaux
nClose = itk.BinaryMorphologicalClosingImageFilter.US3US3.New(nOpen, SafeBorder=True)
nk2 = nClose.GetKernel()
nr2 = nk2.GetRadius()
nr2.Fill(30)
nr2[2] = 10
nk2.SetRadius(nr2)
nk2.CreateStructuringElement()
nClose.SetKernel(nk2)


# les granules
# gHconvex = itk.HConvexImageFilter.US3US3(median, Height=25)
# gThreshold = itk.BinaryThresholdImageFilter.US3US3.New(gHconvex, LowerThreshold=1)

# essai de top-hat
gkernel = itk.BinaryBallStructuringElement.US3(Radius=10)
gr = gkernel.GetRadius()
gr.SetElement(2, 5)
gkernel.SetRadius(gr)
gkernel.CreateStructuringElement()
gTopHat = itk.WhiteTopHatImageFilter.US3US3.New(median, Kernel=gkernel)
gThreshold = itk.BinaryThresholdImageFilter.US3US3.New(gTopHat, LowerThreshold=70)

gAnd = itk.AndImageFilter.US3US3US3.New(nClose, gThreshold)
# supprime les elts trop petits
gkernel = itk.BinaryBallStructuringElement.US3(Radius=2)
gr = gkernel.GetRadius()
gr.SetElement(2, 1)
gkernel.SetRadius(gr)
gkernel.CreateStructuringElement()
gOpen = itk.OpeningByReconstructionImageFilter.US3US3.New(gAnd, Kernel=gkernel)
gConnected = itk.ConnectedComponentImageFilter.US3US3.New(gOpen)
granules = itk.RelabelComponentImageFilter.US3US3.New(gConnected)

gShape = itk.LabelShapeImageFilter.US3.New(granules)
nShape = itk.LabelShapeImageFilter.US3.New(noyaux)

# nPad = itk
# nPad = itk.ConstantPadImageFilter.US3US3.New(nClose, PadBound=1)
# nInvert = itk.InvertIntensityImageFilter.US3US3.New(nPad)
# nDistance = itk.DanielssonDistanceMapImageFilter.US3US3.New(nInvert)
# ns = itk.Size[3]()
# ns.Fill(1)
# nCrop = itk.CropImageFilter.US3US3.New(nDistance, LowerBoundaryCropSize=ns, UpperBoundaryCropSize=ns)
# nInvDist = itk.InvertIntensityImageFilter.US3US3.New(nCrop)
# reader.SetFileName("emb-01ZOOM.tif")


# gShape.Update()
# nShape.Update()


#fin de l'executable
#ci dessous la generation de fichiers resultats
gCast = itk.CastImageFilter.US3UC3.New(gShape)
gWriter = itk.ImageFileWriter.UC3.New(gCast)

nCast = itk.CastImageFilter.US3UC3.New(nShape)
nWriter = itk.ImageFileWriter.UC3.New(nCast)
for fName in sys.argv[1:] :
  reader.SetFileName(fName)
  
  # spacing is wrong... let's fix it
  
  gWriter.SetFileName(fName[:-4]+"-granules.tif")
  gWriter.Update()
  
  nWriter.SetFileName(fName[:-4]+"-noyaux.tif")
  nWriter.Update()

  for i in range(1, nShape.GetNumberOfLabels()) :
    f = file("noyaux.txt", 'a')
    f.write(fName+"\t")
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
    f.write(fName+"\t")
    f.write(str(i)+"\t")
    f.write(str(gShape.GetVolume(i))+"\t")
    for j in range(0, 3) :
      if j != 0 :
        f.write(",")
      f.write(str(gShape.GetCenterOfGravity(i).GetElement(j)))
    f.write("\t")
    f.write("\n")
    f.close()
    
  print fName, "done."
	
# bgr = itk.BinaryThresholdImageFilter.US3US3.New(grecons, LowerThreshold=1, InsideValue=4)
# a = itk.AddImageFilter.US3US3US3.New(noyaux, bgr)
# v = Viewer(a)
# v.AdaptColorAndOpacity()
# 
# 
# v.SetInput(granules.GetOutput())
# v.AdaptColorAndOpacity()



def GetRange(img, imageType="US3") :
  import itk
  img.Update()
  try :
    comp = itk.MinimumMaximumImageCalculator[imageType].New(Image=img.GetOutput())
  except TypeError:
    comp = itk.MinimumMaximumImageCalculator[imageType].New(Image=img)
  comp.Compute()
  return (comp.GetMinimum(), comp.GetMaximum())


class Viewer :
  def __init__(self, filt=None, Input=None, MinOpacity=0.0, MaxOpacity=0.2, imageType='US3') :
    import qt
    import vtk
    import itkvtk
    from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    self.__imageType__ = imageType
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
