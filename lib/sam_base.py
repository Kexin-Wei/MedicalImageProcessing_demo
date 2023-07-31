import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from segment_anything import sam_model_registry, SamPredictor
from lib.utility.define_class import STR_OR_PATH


class BasicSAM:
    def __init__(self, model_type: str = "vit_h"):
        if model_type == "vit_h":
            self.sam_checkpoint = "../sam_vit_h_4b8939.pth"
        elif model_type == "vit_b":
            self.sam_checkpoint = "../sam_vit_b_01ec64.pth"
        elif model_type == "vit_l":
            self.sam_checkpoint = "../sam_vit_l_0b3195.pth"
        elif model_type == 'medsam_vit_b':
            model_type = "vit_b"
            self.sam_checkpoint = "../medsam_vit_b.pth"
        else:
            print(
                "No such a model type supproted in SAM, select vit_h by default."
                " Avaliable selections are vit_h, vit_b, vit_l"
            )
            model_type = "vit_h"
            self.sam_checkpoint = "../sam_vit_h_4b8939.pth"

        self.device = "cuda"
        self.sam = sam_model_registry[model_type](checkpoint=self.sam_checkpoint)
        self.sam.to(device=self.device)
        self.predictor = SamPredictor(self.sam)
        print("SAM Model set up finished.")

    def skipPredictAndSaveEmpty(self, imageFile: Path, figSavePath: STR_OR_PATH):
        image = cv2.imread(str(imageFile))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = np.zeros((image.shape[0], image.shape[1]))
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        plt.title(f"{imageFile.name}: No Mask", fontsize=18)
        plt.savefig(str(figSavePath) + "_mask_1.png")
        return mask

    def predictOneImg(
        self,
        imageFile: Path,
        figSavePath: STR_OR_PATH,
        onlyFirstMask: bool = False,
    ):
        image = cv2.imread(str(imageFile))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # plt.figure()
        # plt.imshow(image)
        # plt.axis('on')
        # plt.show()
        self.predictor.set_image(image)

        center_point = np.array(image.shape) / 2
        input_point = np.array([[center_point[0], center_point[1]]], dtype=int)
        input_label = np.array([1])

        # plt.figure()
        # plt.imshow(image)
        # show_points(input_point, input_label, plt.gca())
        # plt.axis('on')
        # plt.show()

        masks, scores, logits = self.predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=True,
        )

        for i, (mask, score) in enumerate(zip(masks, scores)):
            plt.figure(figsize=(10, 10))
            plt.imshow(image)
            self.show_mask(mask, plt.gca())
            self.show_points(input_point, input_label, plt.gca())
            plt.title(f"{imageFile.name}: Mask {i+1}, Score: {score:.3f}", fontsize=18)
            plt.savefig(str(figSavePath) + f"_mask_{i+1}.png")
            if onlyFirstMask:
                break
        plt.close("all")
        return masks, scores

    @staticmethod
    def show_mask(mask, ax, random_color=False):
        if random_color:
            color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
        else:
            color = np.array([30 / 255, 144 / 255, 255 / 255, 0.6])
        h, w = mask.shape[-2:]
        mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
        ax.imshow(mask_image)

    @staticmethod
    def show_points(coords, labels, ax, marker_size=375):
        pos_points = coords[labels == 1]
        neg_points = coords[labels == 0]
        ax.scatter(
            pos_points[:, 0],
            pos_points[:, 1],
            color="green",
            marker="*",
            s=marker_size,
            edgecolor="white",
            linewidth=1.25,
        )
        ax.scatter(
            neg_points[:, 0],
            neg_points[:, 1],
            color="red",
            marker="*",
            s=marker_size,
            edgecolor="white",
            linewidth=1.25,
        )

    @staticmethod
    def show_box(box, ax):
        x0, y0 = box[0], box[1]
        w, h = box[2] - box[0], box[3] - box[1]
        ax.add_patch(
            plt.Rectangle(
                (x0, y0), w, h, edgecolor="green", facecolor=(0, 0, 0, 0), lw=2
            )
        )
