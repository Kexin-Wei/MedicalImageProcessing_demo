import vtk
from pathlib import Path
from lib.folder.basic import FolderMg


data_path = Path("data").joinpath("biopsy-plan")
result_path = Path("result").joinpath("biopsy-plan")
mg = FolderMg(data_path)
mg.ls()

for f in mg.files:
    if "t2" in f.name.lower():
        prostate_file = f
    else:
        specimen_file = f
output_png_file = result_path.joinpath(f"biopsy-plan{prostate_file.name}.png")


def cude_center_of_two_points(p1: tuple, p3: tuple):
    assert len(p1) == 2 and len(p3) == 2, "p1 and p3 must be a tuple of length 2"
    x1, y1 = p1
    x2, y2 = p3
    return (x1 + x2) / 2, (y1 + y2) / 2


def fourth_center_of_later(p1: tuple, p3: tuple):
    assert len(p1) == 2 and len(p3) == 2, "p1 and p3 must be a tuple of length 2"
    p_mid = cude_center_of_two_points(p1, p3)
    p_3_mid = cude_center_of_two_points(p3, p_mid)
    return p_3_mid


def four_cude_center_from_two_points(p1: tuple, p3: tuple, left: bool = True):
    assert len(p1) == 2 and len(p3) == 2, "p1 and p3 must be a tuple of length 2"
    x1, y1 = p1
    x2, y2 = p3
    p2 = (x2, y1)
    p4 = (x1, y2)
    p_mid = cude_center_of_two_points(p1, p3)
    centers = []
    if left:
        centers.append(cude_center_of_two_points(p1, p_mid))
        centers.append(cude_center_of_two_points(p2, p_mid))
        centers.append(cude_center_of_two_points(p3, p_mid))
        centers.append(fourth_center_of_later(p4, p_mid))
    else:  # right
        centers.append(cude_center_of_two_points(p1, p_mid))
        centers.append(cude_center_of_two_points(p2, p_mid))
        centers.append(cude_center_of_two_points(p4, p_mid))
        centers.append(fourth_center_of_later(p3, p_mid))
    return centers


def ten_cores(p1: tuple, p3: tuple):
    assert len(p1) == 2 and len(p3) == 2, "p1 and p3 must be a tuple of length 2"
    x1, y1 = p1
    x2, y2 = p3
    p2 = (x2, y1)
    p4 = (x1, y2)

    tops = []
    p_mid = cude_center_of_two_points(p1, p3)
    p_1_mid = cude_center_of_two_points(p1, p_mid)
    p_2_mid = cude_center_of_two_points(p2, p_mid)
    tops.append(fourth_center_of_later(p_mid, p_1_mid))
    tops.append(fourth_center_of_later(p_mid, p_2_mid))

    bots = []
    p14 = cude_center_of_two_points(p1, p4)
    p34 = cude_center_of_two_points(p3, p4)
    left_bots = four_cude_center_from_two_points(p14, p34, left=True)
    right_bots = four_cude_center_from_two_points(p_mid, p3, left=False)
    bots.extend(left_bots)
    bots.extend(right_bots)

    all_points = []
    all_points.extend(tops)
    all_points.extend(bots)
    return all_points


def twelve_cores(p1: tuple, p3: tuple):
    assert len(p1) == 2 and len(p3) == 2, "p1 and p3 must be a tuple of length 2"
    x1, y1 = p1
    x2, y2 = p3
    p2 = (x2, y1)
    p4 = (x1, y2)
    p_mid = cude_center_of_two_points(p1, p3)

    tops = []
    p12 = cude_center_of_two_points(p1, p2)
    p_1_mid = cude_center_of_two_points(p1, p_mid)
    p_12_1_mid = cude_center_of_two_points(p12, p_1_mid)
    tops.append(p_12_1_mid)
    p14 = cude_center_of_two_points(p1, p4)
    tops.append(fourth_center_of_later(p14, p_1_mid))

    p_2_mid = cude_center_of_two_points(p2, p_mid)
    p_12_2_mid = cude_center_of_two_points(p12, p_2_mid)
    tops.append(p_12_2_mid)
    p23 = cude_center_of_two_points(p2, p3)
    tops.append(fourth_center_of_later(p23, p_2_mid))

    bots = []
    p34 = cude_center_of_two_points(p3, p4)
    left_bots = four_cude_center_from_two_points(p14, p34, left=True)
    right_bots = four_cude_center_from_two_points(p_mid, p3, left=False)
    bots.extend(left_bots)
    bots.extend(right_bots)

    all_points = []
    all_points.extend(tops)
    all_points.extend(bots)
    return all_points


def add_specimen(p: tuple):
    assert len(p) == 2, "p must be a tuple of length 2"
    x, y = p
    specimen_reader = vtk.vtkSTLReader()
    specimen_reader.SetFileName(str(specimen_file))

    transform = vtk.vtkTransform()
    transform.Translate(x, y, 0)

    transform_filter = vtk.vtkTransformPolyDataFilter()
    transform_filter.SetInputConnection(specimen_reader.GetOutputPort())
    transform_filter.SetTransform(transform)
    transform_filter.Update()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(transform_filter.GetOutput())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(colors.GetColor3d("Blue"))
    return actor


colors = vtk.vtkNamedColors()

prostate_reader = vtk.vtkSTLReader()
prostate_reader.SetFileName(str(prostate_file))
prostate_reader.Update()
prostate_poly = prostate_reader.GetOutput()


mapper1 = vtk.vtkPolyDataMapper()
mapper1.SetInputData(prostate_reader.GetOutput())
actor1 = vtk.vtkActor()
actor1.SetMapper(mapper1)
actor1.GetProperty().SetColor(colors.GetColor3d("Red"))
actor1.GetProperty().SetOpacity(0.5)

prostate_bounds = actor1.GetBounds()
print(prostate_bounds)
p1 = (prostate_bounds[1], prostate_bounds[2])
p2 = (prostate_bounds[0], prostate_bounds[3])

core_points = ten_cores(p1, p2)

# core_points = twelve_cores(p1, p2)
actors = []
for p in core_points:
    actors.append(add_specimen(p))


renderer = vtk.vtkRenderer()
renderer.AddActor(actor1)
for a in actors:
    renderer.AddActor(a)

window = vtk.vtkRenderWindow()
window.AddRenderer(renderer)
interactor = vtk.vtkRenderWindowInteractor()
interactor.SetRenderWindow(window)
window.Render()
interactor.Start()
