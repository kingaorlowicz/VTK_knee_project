import vtk 
import os
from PyQt5.QtWidgets import( QApplication, QMainWindow, QVBoxLayout, QScrollArea,
    QSlider, QLabel, QWidget, QHBoxLayout, QFrame)
from PyQt5.QtCore import Qt

def LoadVtkMeshes(folder_path): # wczytanie modeli VTK z folderu
    VtkMeshes = []
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".vtk"):
            file_path = os.path.join(folder_path, file_name)
            reader = vtk.vtkPolyDataReader()
            reader.SetFileName(file_path)
            reader.Update()
            VtkMeshes.append((reader.GetOutput(), file_name))
    return VtkMeshes

def LoadRawData(file_path): # wczytanie danych raw
    reader = vtk.vtkNrrdReader()
    reader.SetFileName(file_path)
    reader.Update()
    return reader

def CreateMeshActors(VtkMeshes, colors): # stworzenie aktorów z modeli VTK
    actors = []
    predefined_colors = [
        "Tomato", "Banana", "Mint", "Peacock", "Salmon",
        "Lavender", "Wheat", "DarkCyan", "Pink", "LimeGreen",
        "AliceBlue", "Aqua", "Aquamarine", "Azure", "Beige",
        "Bisque", "DarkOliveGreen", "Blue", "Brown", "BurlyWood",
        "CadetBlue", "Chartreuse", "Chocolate", "Coral", "CornflowerBlue",
        "Crimson", "DarkBlue", "DarkCyan", "DarkGoldenRod", "DarkGray",
        "DarkGreen", "DarkKhaki", "DarkMagenta", "DarkOrange", "DarkOrchid",
        "DarkRed", "DarkSalmon", "DarkSeaGreen", "DarkSlateBlue", "DarkSlateGray",
        "DarkTurquoise", "DarkViolet", "SaddleBrown", "DeepSkyBlue", "DimGray",
        "DodgerBlue", "FireBrick", "FloralWhite", "ForestGreen", "SeaGreen"
    ]
    for i, (mesh, name) in enumerate(VtkMeshes): 
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(mesh)

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        ColorName = predefined_colors[i % len(predefined_colors)]
        actor.GetProperty().SetColor(colors.GetColor3d(ColorName))
        actor.GetProperty().SetOpacity(1.0)  # domyslna przezroczystosc 100%
        actor.name = name
        actors.append(actor)
    return actors

def CreateBWlut(): # stworzenie LookupTable (czarno-biały)
    bwLut = vtk.vtkLookupTable()
    bwLut.SetTableRange(0, 2000)
    bwLut.SetSaturationRange(0, 0)
    bwLut.SetHueRange(0, 0)
    bwLut.SetValueRange(0, 1)
    bwLut.Build()
    return bwLut

def CreateRawActor(SliceID, orientation, raw_data_reader, bw_lut, DataExtent): # stworzenie aktora z danych raw
    ImageToMapColors = vtk.vtkImageMapToColors()
    ImageToMapColors.SetInputConnection(raw_data_reader.GetOutputPort())
    ImageToMapColors.SetLookupTable(bw_lut) # ustawienie przygotowanej LookupTable
    ImageToMapColors.Update() 

    RawActor = vtk.vtkImageActor()
    RawActor.GetMapper().SetInputConnection(ImageToMapColors.GetOutputPort())
    RawActor.GetProperty().SetOpacity(1.0)  # domyslna przezroczystosc 100%
    # stworzenie aktora w zależności od orientacji
    if orientation == 'sagittal':
        RawActor.SetDisplayExtent(
            SliceID, SliceID,
            DataExtent[2], DataExtent[3],
            DataExtent[4], DataExtent[5],
        )
    elif orientation == 'coronal':
        RawActor.SetDisplayExtent(
            DataExtent[0], DataExtent[1],
            SliceID, SliceID,
            DataExtent[4], DataExtent[5],
        )
    elif orientation == 'axial':
        RawActor.SetDisplayExtent(
            DataExtent[0], DataExtent[1],
            DataExtent[2], DataExtent[3],
            SliceID, SliceID,
        )

    return RawActor

#obsługa klawiatury (przemieszczanie przekrojów)
def Keypress(obj, event, sagittal, coronal, axial, RenderWindow, sagittal_renderer,
    coronal_renderer, axial_renderer): 
    key = obj.GetKeySym()
    if key == "Right":
        extent = list(sagittal.GetDisplayExtent())
        extent[0] += 1
        extent[1] += 1
        sagittal.SetDisplayExtent(*extent)
    elif key == "Left":
        extent = list(sagittal.GetDisplayExtent())
        extent[0] -= 1
        extent[1] -= 1
        sagittal.SetDisplayExtent(*extent)
    elif key == "Up":
        extent = list(coronal.GetDisplayExtent())
        extent[2] += 1
        extent[3] += 1
        coronal.SetDisplayExtent(*extent)
    elif key == "Down":
        extent = list(coronal.GetDisplayExtent())
        extent[2] -= 1
        extent[3] -= 1
        coronal.SetDisplayExtent(*extent)
    elif key == "a":
        extent = list(axial.GetDisplayExtent())
        extent[4] += 1
        extent[5] += 1
        axial.SetDisplayExtent(*extent)
    elif key == "d":
        extent = list(axial.GetDisplayExtent())
        extent[4] -= 1
        extent[5] -= 1
        axial.SetDisplayExtent(*extent) 
    RenderWindow.Render() 
    sagittal_renderer.Render() 
    coronal_renderer.Render()   
    axial_renderer.Render()

def Visualize(raw_data_reader, VtkMeshes): # stworzenie okna z wizualizacją
    colors = vtk.vtkNamedColors()

    # Główny renderer
    MainRenderer = vtk.vtkRenderer()
    RenderWindow = vtk.vtkRenderWindow()
    RenderWindow.AddRenderer(MainRenderer)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(RenderWindow)

    #Dodanie aktorów VTK do głównego renderera
    VtkActors = CreateMeshActors(VtkMeshes, colors)
    for actor in VtkActors:
        MainRenderer.AddActor(actor)

    DataExtent = raw_data_reader.GetDataExtent() # pobranie rozmiaru danych raw

    bw_lut = CreateBWlut() 

    # Stworzenie aktorów dla poszczególnych przekrojów
    sagittal = CreateRawActor((DataExtent[0] + DataExtent[1]) // 2, 'sagittal', raw_data_reader, bw_lut, DataExtent)
    coronal = CreateRawActor((DataExtent[2] + DataExtent[3]) // 2, 'coronal', raw_data_reader, bw_lut, DataExtent)
    axial = CreateRawActor((DataExtent[4] + DataExtent[5]) // 2, 'axial', raw_data_reader, bw_lut, DataExtent)

    # Dodanie aktorów raw (przekroje) do głównego renderera
    MainRenderer.AddActor(sagittal)
    MainRenderer.AddActor(coronal)
    MainRenderer.AddActor(axial)

    for actor in VtkActors:
        MainRenderer.AddActor(actor)
    
    #kolor tła
    background_color = [0.404, 0.341, 0.459]
    MainRenderer.SetBackground(background_color)
    MainRenderer.ResetCamera()

    #rozmiar okna
    RenderWindow.SetSize(1200, 900)

    #Inicjalizacja interactora
    interactor.Initialize()
    RenderWindow.Render()

    sagittal_renderer, coronal_renderer, axial_renderer = CreateSectionalRenderers(sagittal, coronal, axial, colors)

    interactor.AddObserver("KeyPressEvent", lambda obj, event: 
        Keypress(obj, event, sagittal, coronal, axial, RenderWindow, sagittal_renderer, coronal_renderer, axial_renderer))

    return RenderWindow, interactor, VtkActors, sagittal_renderer, coronal_renderer, axial_renderer

def CreateSectionalRenderers(sagittal, coronal, axial, colors):
    # Aktorzy dla widoków przekrojów
    sagittal_renderer = vtk.vtkRenderer()
    coronal_renderer = vtk.vtkRenderer()
    axial_renderer = vtk.vtkRenderer()

    sagittal_renderer.AddActor(sagittal)
    coronal_renderer.AddActor(coronal)
    axial_renderer.AddActor(axial)

    # kolor tła
    background_color = [0.404, 0.341, 0.459]
    sagittal_renderer.SetBackground(background_color)
    coronal_renderer.SetBackground(background_color)
    axial_renderer.SetBackground(background_color)

    # Ustawienie kamer dla widoków przekrojów
    sagittal_camera = sagittal_renderer.GetActiveCamera()
    sagittal_camera.SetViewUp(0, 0, 1)
    sagittal_camera.SetPosition(1, 0, 0)
    sagittal_camera.SetFocalPoint(0, 0, 0)
    sagittal_renderer.ResetCamera()

    coronal_camera = coronal_renderer.GetActiveCamera()
    coronal_camera.SetViewUp(0, 0, 1)
    coronal_camera.SetPosition(0, -1, 0)
    coronal_camera.SetFocalPoint(0, 0, 0)
    coronal_renderer.ResetCamera()

    axial_camera = axial_renderer.GetActiveCamera()
    axial_camera.SetViewUp(0, -1, 0)
    axial_camera.SetPosition(0, 0, 1)
    axial_camera.SetFocalPoint(0, 0, 0)
    axial_renderer.ResetCamera()

    # zakaz interakcji z widokami przekrojów
    sagittal_renderer.SetInteractive(0)
    coronal_renderer.SetInteractive(0)
    axial_renderer.SetInteractive(0)

    return sagittal_renderer, coronal_renderer, axial_renderer

def AddViewpointsToRenderWindow(renWin, renderers, labels): # dodanie viewpointów do okna
    viewport_coords = [ # pozycje viewpointów
        [0.75, 0.67, 1.0, 1.0],
        [0.75, 0.34, 1.0, 0.67],
        [0.75, 0.0, 1.0, 0.34],
    ]

    for i, renderer in enumerate(renderers):
        renderer.SetViewport(viewport_coords[i])
        renWin.AddRenderer(renderer)

        # podpisy viewpointów
        text_actor = vtk.vtkTextActor()
        text_actor.SetInput(labels[i])
        text_prop = text_actor.GetTextProperty()
        text_prop.SetFontSize(24)
        text_prop.SetColor(1, 1, 1)
        text_actor.SetPosition(10, 10)
        renderer.AddActor2D(text_actor)

class OpacityControlApp(QMainWindow): # control panel do zmiany przezroczystości
    def __init__(self, VtkActors, parent=None): # inicjalizacja
        super(OpacityControlApp, self).__init__(parent)
        self.VtkActors = VtkActors
        self.individual_sliders = []

        self.setWindowTitle("Control Panel")
        self.setGeometry(100, 100, 600, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_content.setLayout(scroll_layout)

        # slajder globalny (dla wszystkich aktorów)
        global_label = QLabel("Opacity of all")
        global_label.setStyleSheet("font-size: 24px;")
        global_slider = QSlider(Qt.Horizontal)
        global_slider.setMinimum(0)
        global_slider.setMaximum(10)
        global_slider.setValue(10)
        global_value_label = QLabel(f"{int(global_slider.value() * 10)}%")
        global_value_label.setStyleSheet("font-size: 24px;")
        global_slider.valueChanged.connect(lambda value: self.UpdateGlobalOpacity(value, global_value_label))

        global_horizontal_layout = QHBoxLayout()
        global_horizontal_layout.addWidget(global_slider)
        global_horizontal_layout.addWidget(global_value_label)

        scroll_layout.addWidget(global_label)
        scroll_layout.addLayout(global_horizontal_layout)

        # slajdery indywidualne (dla każdego aktora)
        for actor in self.VtkActors:
            vertical_layout = QVBoxLayout()

            label = QLabel(actor.name)
            label.setStyleSheet("font-size: 24px;") 
            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(10)
            slider.setValue(int(actor.GetProperty().GetOpacity() * 10)) 
            value_label = QLabel(f"{int(actor.GetProperty().GetOpacity() * 100)}%") 
            value_label.setStyleSheet("font-size: 24px;") 
            slider.valueChanged.connect(lambda value, a=actor, l=value_label: self.UpdateOpacity(a, value, l))
            self.individual_sliders.append((slider, value_label))

            horizontal_layout = QHBoxLayout()
            horizontal_layout.addWidget(slider)
            horizontal_layout.addWidget(value_label)

            vertical_layout.addWidget(label)
            vertical_layout.addLayout(horizontal_layout)

            scroll_layout.addLayout(vertical_layout)

        scroll_area.setWidget(scroll_content)
        self.layout.addWidget(scroll_area)

        self.CustomSlider()

    def CustomSlider(self): # wygląd slidera
        custom_slider_style = """
        QSlider::groove:horizontal {
            background: #c8b8d9;
            height: 16px;
        }
        QSlider::handle:horizontal {
            background: #675779;
            border: 1px solid #5c5c5c;
            width: 30px;
            height: 30px;
            margin: -8px 0;
            border-radius: 15px;
        }
        QScrollArea {
            background-color: #e7dcf2;
            color: #000000;
        }
        QWidget {
            background-color: #e7dcf2;
            color: #000000;
            font-size: 30px;
        }
        """
        self.central_widget.setStyleSheet(custom_slider_style)

    def UpdateOpacity(self, actor, value, value_label): # zmiana opacity pojedynczego aktora
        NewOpacity = value / 10.0
        actor.GetProperty().SetOpacity(NewOpacity)
        actor.GetMapper().Update()
        value_label.setText(f"{int(NewOpacity * 100)}%")

    def UpdateGlobalOpacity(self, value, global_value_label): # zmiana opacity wszystkich aktorów
        NewOpacity = value / 10.0
        for actor in self.VtkActors:
            actor.GetProperty().SetOpacity(NewOpacity)
        for slider, value_label in self.individual_sliders:
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)
            value_label.setText(f"{int(NewOpacity * 100)}%")
        global_value_label.setText(f"{int(NewOpacity * 100)}%")

if __name__ == "__main__": 
    app = QApplication([])

    #ścieżka do pliku z danymi "I.nrrd"
    RawDataFile = "C:/Users/kinga/Desktop/semestr 5/VTK/knee-2016-09/Data/I.nrrd" 
    
    #ścieżka do folderu z modelami (Data lub Models - obojętne)
    MeshFolder = "C:/Users/kinga/Desktop/semestr 5/VTK/knee-2016-09/Data/Models"

    RawDataReader = LoadRawData(RawDataFile) 
    VtkMeshes = LoadVtkMeshes(MeshFolder)

    (RenderWindow, interactor, VtkActors,
            sagittal_renderer, coronal_renderer, axial_renderer) = Visualize(RawDataReader, VtkMeshes)

    # Okno głowne i viewpointy
    AddViewpointsToRenderWindow(RenderWindow, [sagittal_renderer, coronal_renderer, axial_renderer], 
                                                ["Sagittal", "Coronal", "Axial"])

    # Control panel
    opacity_control = OpacityControlApp(VtkActors)
    opacity_control.show()

    # wyjście z aplikacji
    RenderWindow.AddObserver("WindowCloseEvent", lambda o, e: app.quit())
    opacity_control.closeEvent = lambda event: app.quit()

    # Start 
    interactor.Start()
    app.exec_()