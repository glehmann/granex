#!/usr/bin/python

import itk, sys
itk.auto_progress=True
PT = itk.UC
LPT = itk.UL
dim = 3
IT = itk.Image[PT, dim]
LIT = itk.Image[LPT, dim]
reader = itk.ImageFileReader[IT].New()
# spacing is wrong... let's fix it
spacing = itk.Vector[itk.D, dim]()
spacing.Fill(1)
spacing[2] = 3
changeInfo = itk.ChangeInformationImageFilter[IT].New(reader, OutputSpacing=spacing, ChangeSpacing=True)
# resample image to be isotropic
resample = itk.IsotropicResolutionImageFilter[IT, IT].New(changeInfo) #, MaximumIncrease=2)

# un peu de nettoyage
median = itk.MedianImageFilter[IT, IT].New(resample, Radius=2)
# r = median.GetRadius()
# r.SetElement(2, 1)

# selectionne le noyau
nThreshold = itk.BinaryThresholdImageFilter[IT, IT].New(median, LowerThreshold=30)
# supprime tous les petits trucs qui trainent dans l'image
kernel = itk.BinaryBallStructuringElement[PT, dim]()
r = kernel.GetRadius()
r.Fill(5)
# r.SetElement(2, 1)
kernel.SetRadius(r)
kernel.CreateStructuringElement()
nOpen = itk.OpeningByReconstructionImageFilter[IT, IT, kernel].New(nThreshold, Kernel=kernel)
# il faut faire une fermeture pour lisser les noyaux
nk2 = itk.BinaryBallStructuringElement[PT, dim]()
nr2 = nk2.GetRadius()
nr2.Fill(30)
nr2[2] = 10
nk2.SetRadius(nr2)
nk2.CreateStructuringElement()
nClose = itk.BinaryMorphologicalClosingImageFilter[IT, IT, nk2].New(nOpen, SafeBorder=True, Kernel=nk2)
nConnected = itk.ConnectedComponentImageFilter[IT, LIT].New(nClose)
noyaux = itk.RelabelComponentImageFilter[LIT, IT].New(nConnected)


# les granules
# gHconvex = itk.HConvexImageFilter.US3US3(median, Height=25)
# gThreshold = itk.BinaryThresholdImageFilter.US3US3.New(gHconvex, LowerThreshold=1)

# essai de top-hat
gkernel = itk.BinaryBallStructuringElement[PT, dim]()
gr = gkernel.GetRadius()
gr.Fill(10)
gr.SetElement(2, 5)
gkernel.SetRadius(gr)
gkernel.CreateStructuringElement()
gTopHat = itk.WhiteTopHatImageFilter[IT, IT, gkernel].New(median, Kernel=gkernel)
gThreshold = itk.BinaryThresholdImageFilter[IT, IT].New(gTopHat, LowerThreshold=70)

# with an h-convex
gHConvex = itk.HConvexImageFilter[IT, IT].New(median, Height=25)
gThreshold2 = itk.BinaryThresholdImageFilter[IT, IT].New(gHConvex, LowerThreshold=1)

gAnd = itk.AndImageFilter[IT, IT, IT].New(nClose, gThreshold2)
# supprime les elts trop petits
gkernel = itk.BinaryBallStructuringElement[PT, dim]()
gr = gkernel.GetRadius()
gr.Fill(2)
gr.SetElement(2, 1)
gkernel.SetRadius(gr)
gkernel.CreateStructuringElement()
gOpen = itk.OpeningByReconstructionImageFilter[IT, IT, gkernel].New(gAnd, Kernel=gkernel)
gConnected = itk.ConnectedComponentImageFilter[IT, LIT].New(gOpen)
granules = itk.RelabelComponentImageFilter[LIT, IT].New(gConnected)

gShape = itk.LabelShapeImageFilter[IT].New(granules)
nShape = itk.LabelShapeImageFilter[IT].New(noyaux)

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
# gCast = itk.CastImageFilter.US3UC3.New(gShape)
gWriter = itk.ImageFileWriter[IT].New(gShape)

# nCast = itk.CastImageFilter.US3UC3.New(nShape)
nWriter = itk.ImageFileWriter[IT].New(nCast)

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
