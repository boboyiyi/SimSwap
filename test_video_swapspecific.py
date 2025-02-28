
import cv2
import torch
import fractions
import numpy as np
from PIL import Image
import torch.nn.functional as F
from torchvision import transforms
from models.models import create_model
from options.test_options import TestOptions
from insightface_func.face_detect_crop_multi import Face_detect_crop
from util.videoswap_specific import video_swap
import os

def lcm(a, b): return abs(a * b) / fractions.gcd(a, b) if a and b else 0

transformer = transforms.Compose([
        transforms.ToTensor(),
        #transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

transformer_Arcface = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

# detransformer = transforms.Compose([
#         transforms.Normalize([0, 0, 0], [1/0.229, 1/0.224, 1/0.225]),
#         transforms.Normalize([-0.485, -0.456, -0.406], [1, 1, 1])
#     ])


if __name__ == '__main__':
    opt = TestOptions().parse()
    pic_specific = opt.pic_specific_path
    start_epoch, epoch_iter = 1, 0
    crop_size = 224

    torch.nn.Module.dump_patches = True
    model = create_model(opt)
    model.eval()


    app = Face_detect_crop(name='antelope', root='./insightface_func/models')
    app.prepare(ctx_id= 0, det_thresh=0.6, det_size=(640,640))

    pic_a = opt.pic_a_path
    # img_a = Image.open(pic_a).convert('RGB')
    img_a_whole = cv2.imread(pic_a)
    img_a_align_crop, _ = app.get(img_a_whole,crop_size)
    img_a_align_crop_pil = Image.fromarray(cv2.cvtColor(img_a_align_crop[0],cv2.COLOR_BGR2RGB)) 
    img_a = transformer_Arcface(img_a_align_crop_pil)
    img_id = img_a.view(-1, img_a.shape[0], img_a.shape[1], img_a.shape[2])

    # pic_b = opt.pic_b_path
    # img_b_whole = cv2.imread(pic_b)
    # img_b_align_crop, b_mat = app.get(img_b_whole,crop_size)
    # img_b_align_crop_pil = Image.fromarray(cv2.cvtColor(img_b_align_crop,cv2.COLOR_BGR2RGB)) 
    # img_b = transformer(img_b_align_crop_pil)
    # img_att = img_b.view(-1, img_b.shape[0], img_b.shape[1], img_b.shape[2])

    # convert numpy to tensor
    img_id = img_id.cuda()
    # img_att = img_att.cuda()

    #create latent id
    img_id_downsample = F.interpolate(img_id, scale_factor=0.5)
    latend_id = model.netArc(img_id_downsample)
    latend_id = F.normalize(latend_id, p=2, dim=1)


    # The specific person to be swapped
    specific_person_whole = cv2.imread(pic_specific)
    specific_person_align_crop, _ = app.get(specific_person_whole,crop_size)
    specific_person_align_crop_pil = Image.fromarray(cv2.cvtColor(specific_person_align_crop[0],cv2.COLOR_BGR2RGB)) 
    specific_person = transformer_Arcface(specific_person_align_crop_pil)
    specific_person = specific_person.view(-1, specific_person.shape[0], specific_person.shape[1], specific_person.shape[2])
    specific_person = specific_person.cuda()
    specific_person_downsample = F.interpolate(specific_person, scale_factor=0.5)
    specific_person_id_nonorm = model.netArc(specific_person_downsample)

    video_swap(opt.video_path, latend_id,specific_person_id_nonorm, opt.id_thres, \
        model, app, opt.output_path,temp_results_dir=opt.temp_path,no_simswaplogo=opt.no_simswaplogo)

