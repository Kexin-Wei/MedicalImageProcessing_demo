"""2023.07.17 Kexin
using [Segment-Anything](https://github.com/facebookresearch/segment-anything) pretrained model to segment prostate mri slice by slice
"""
# %%
import torch
import torchvision
import numpy as np
import matplotlib.pyplot as plt
import cv2
from pathlib import Path
from lib.folder import FolderMg
from segment_anything import sam_model_registry, SamPredictor

print("PyTorch version:", torch.__version__)
print("Torchvision version:", torchvision.__version__)
print("CUDA is available:", torch.cuda.is_available())

# %%


def show_mask(mask, ax, random_color=False):
    if random_color:
        color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
    else:
        color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])
    h, w = mask.shape[-2:]
    mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
    ax.imshow(mask_image)


def show_points(coords, labels, ax, marker_size=375):
    pos_points = coords[labels == 1]
    neg_points = coords[labels == 0]
    ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white',
               linewidth=1.25)
    ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white',
               linewidth=1.25)


def show_box(box, ax):
    x0, y0 = box[0], box[1]
    w, h = box[2] - box[0], box[3] - box[1]
    ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green',
                 facecolor=(0, 0, 0, 0), lw=2))


# %%
sam_checkpoint = "../sam_vit_h_4b8939.pth"
model_type = "vit_h"
# model_type = "vit_b"
# model_type = "vit_l"

device = "cuda"
sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
sam.to(device=device)
predictor = SamPredictor(sam)
print("SAM Model set up finished.")

# %%
sourceDataPath = Path("data").joinpath("mri-prostate-slices")
destinationPath  = Path("result").joinpath("mri-prostate-slices")

print("Processing folders:")
sourceMg = FolderMg(sourceDataPath)
for fd in sourceMg.dirs:
    fdMg = FolderMg(fd)
    middleFile = fdMg.files[int(fdMg.nFile / 2)]

    image = cv2.imread(str(middleFile))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # plt.figure()
    # plt.imshow(image)
    # plt.axis('on')
    # plt.show()
    predictor.set_image(image)

    center_point = np.array(image.shape)/2
    input_point = np.array([[center_point[0], center_point[1]]], dtype=int)
    input_label = np.array([1])

    # plt.figure()
    # plt.imshow(image)
    # show_points(input_point, input_label, plt.gca())
    # plt.axis('on')
    # plt.show()

    masks, scores, logits = predictor.predict(
        point_coords=input_point,
        point_labels=input_label,
        multimask_output=True,
    )

    outputFolderPath = destinationPath.joinpath(f"{fd.name}")
    if not outputFolderPath.exists():
        outputFolderPath.mkdir(parents=True)

    for i, (mask, score) in enumerate(zip(masks, scores)):
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        show_mask(mask, plt.gca())
        show_points(input_point, input_label, plt.gca())
        plt.title(f"{middleFile.name}: Mask {i+1}, Score: {score:.3f}", fontsize=18)
        plt.savefig(outputFolderPath.joinpath(f"{middleFile.name}_mask_{i+1}.png"))
    print(f"- {fd.name}")
    plt.close('all')
print("Finished")
