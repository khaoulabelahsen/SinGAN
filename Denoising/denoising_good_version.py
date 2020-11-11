from config import get_arguments
from SinGAN.manipulate import *
from SinGAN.training import *
from SinGAN.imresize import imresize
import SinGAN.functions as functions


if __name__ == '__main__':
    parser = get_arguments()
    parser.add_argument('--input_dir', help='input image dir', default='Input/Images')
    parser.add_argument('--input_name', help='training image name', default="33039_LR.png")#required=True)
    parser.add_argument('--sr_factor', help='super resolution factor', type=float, default=4)
    parser.add_argument('--mode', help='task to be done', default='SR')
    #I've added this
    parser.add_argument('--denoise_scale',help='Denoising',default='-1')
    parser.add_argument('--stop_scale',help='Denoising',default='0')
    opt = parser.parse_args()
    opt = functions.post_config(opt)
    Gs = []
    Zs = []
    reals = []
    NoiseAmp = []
    dir2save = functions.generate_dir2save(opt)
    if dir2save is None:
        print('task does not exist')
    #elif (os.path.exists(dir2save)):
    #    print("output already exist")
    else:
        try:
            os.makedirs(dir2save)
        except OSError:
            pass

        mode = opt.mode
        in_scale, iter_num = functions.calc_init_scale(opt)
        opt.scale_factor = 1 / in_scale
        opt.scale_factor_init = 1 / in_scale
        opt.mode = 'train'
        dir2trained_model = functions.generate_dir2save(opt)
        if (os.path.exists(dir2trained_model)):
            Gs, Zs, reals, NoiseAmp = functions.load_trained_pyramid(opt)
            opt.mode = mode
        else:
            print('*** Train SinGAN for Denoising ***')
            real = functions.read_image(opt)
            opt.min_size = 18
            real = functions.adjust_scales2image_SR(real, opt)
            train(opt, Gs, Zs, reals, NoiseAmp)
            opt.mode = mode
        print('%f' % pow(in_scale, iter_num))
        Zs_sr = []
        reals_sr = []
        NoiseAmp_sr = []
        Gs_sr = []
        real = reals[-1]  # read_image(opt)
        real_ = real
        opt.scale_factor = 1 / in_scale
        opt.scale_factor_init = 1 / in_scale
        #for j in range(1, iter_num + 1, 1):
            #real_ = imresize(real_, pow(1 / opt.scale_factor, 1), opt)
        for j in range(0,1):
            for k in range(int(opt.stop_scale),1):
                reals_sr.append(real_)
                Gs_sr.append(Gs[int(opt.denoise_scale)-k])
                NoiseAmp_sr.append(NoiseAmp[int(opt.denoise_scale)-k])
                z_opt = torch.full(real_.shape, 0, device=opt.device)
                m = nn.ZeroPad2d(5)
                z_opt = m(z_opt)
                Zs_sr.append(z_opt)
        out = SinGAN_generate(Gs_sr, Zs_sr, reals_sr, NoiseAmp_sr, opt, in_s=reals_sr[0], num_samples=1)
        out = out[:, :, 0:int(opt.sr_factor * reals[-1].shape[2]), 0:int(opt.sr_factor * reals[-1].shape[3])]
        #dir2save = functions.generate_dir2save(opt)
        plt.imsave('%s/%s_denoising.png' % ('Output',opt.input_name[:-4]), functions.convert_image_np(out.detach()), vmin=0, vmax=1)