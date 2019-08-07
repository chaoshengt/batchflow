"""  Ronneberger O. et al "`U-Net: Convolutional Networks for Biomedical Image Segmentation
<https://arxiv.org/abs/1505.04597>`_"
"""

from .encoder_decoder import EncoderDecoder


class UNet(EncoderDecoder):
    """ UNet-like model

    **Configuration**

    inputs : dict
        dict with 'images' and 'masks' (see :meth:`~.TFModel._make_inputs`)

    body : dict
        encoder : dict
            num_stages : int
                number of downsampling blocks (default=4)
            blocks : dict
                Parameters for pre-processing blocks:

                filters : int, list of ints or list of lists of ints
                    The number of filters in the output tensor.
                    If int, same number of filters applies to all layers on all stages
                    If list of ints, specifies number of filters in each layer of different stages
                    If list of list of ints, specifies number of filters in different layers on different stages
                    If not given or None, filters parameters in encoder/blocks, decoder/blocks and decoder/upsample
                    default to values which make number of filters double
                    on each stage of encoding and halve on each stage of decoding,
                    provided that `decoder/skip` is `True`. Number of filters on the first stage of encoding will be
                    doubled number of filters in initial_block's output
                    When defining filters manually mind the filters defined in initial_block and head

        decoder : dict
            num_stages : int
                number of upsampling blocks. Defaults to the number of downsamplings.

            factor : None, int or list of ints
                If int, the total upsampling factor for all stages combined.
                If list, upsampling factors for each stage
                If not given or None, defaults to [2]*num_stages

            blocks : dict
                Parameters for post-processing blocks:

                filters : int, list of ints or list of lists of ints
                    same as encoder/blocks/filters

            upsample : dict
                Parameters for upsampling (see :func:`~.layers.upsample`).

                filters : int, list of ints or list of lists of ints
                    same as encoder/blocks/filters

    for more parameters see (see :class:`~.EncoderDecoder`)
    """
    @classmethod
    def default_config(cls):
        config = super().default_config()

        config['common'] = dict(conv=dict(use_bias=False))

        config['initial_block'] = dict(layout='cna cna', kernel_size=3, filters=64)

        config['body/encoder/num_stages'] = 4
        config['body/encoder/blocks'] = dict(layout='cna cna', kernel_size=3, filters=None)
        config['body/embedding'] = None  # identity
        config['body/decoder/num_stages'] = None  # defaults to body/encoder/num_stages
        config['body/decoder/factor'] = None  # defaults to [2] * num_stages
        config['body/decoder/blocks'] = dict(layout='cna cna', kernel_size=3, filters=None)

        config['head'] = dict(layout='cna cna', kernel_size=3, strides=1, filters=64)

        config['loss'] = 'ce'

        return config

    def build_config(self, names=None):
        config = super().build_config(names)

        num_stages = config.get('body/encoder/num_stages')

        initial_block_filters = config.get('initial_block/filters')
        f_0 = initial_block_filters[-1] if isinstance(initial_block_filters, (list, tuple)) else initial_block_filters

        if config.get('body/encoder/blocks/filters') is None:
            config['body/encoder/blocks/filters'] = [f_0*2**(i+1) for i in range(num_stages)]

        if config.get('body/decoder/blocks/filters') is None:
            config['body/decoder/blocks/filters'] = list(reversed([f_0*2**i for i in range(num_stages)]))

        if config.get('body/decoder/upsample/filters') is None:
            config['body/decoder/upsample/filters'] = list(reversed([f_0*2**(i+1) for i in range(num_stages)]))

        return config