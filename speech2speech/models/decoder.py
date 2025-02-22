
 #####################################################################################
 # MIT License                                                                       #
 #                                                                                   #
 # Copyright (C) 2019 Charly Lamothe                                                 #
 #                                                                                   #
 # This file is part of VQ-VAE-Speech.                                               #
 #                                                                                   #
 #   Permission is hereby granted, free of charge, to any person obtaining a copy    #
 #   of this software and associated documentation files (the "Software"), to deal   #
 #   in the Software without restriction, including without limitation the rights    #
 #   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
 #   copies of the Software, and to permit persons to whom the Software is           #
 #   furnished to do so, subject to the following conditions:                        #
 #                                                                                   #
 #   The above copyright notice and this permission notice shall be included in all  #
 #   copies or substantial portions of the Software.                                 #
 #                                                                                   #
 #   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
 #   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
 #   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
 #   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
 #   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
 #   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
 #   SOFTWARE.                                                                       #
 #####################################################################################

from .residual_stack import ResidualStack

import sys

import torch
import torch.nn as nn
import torch.nn.functional as F


class Decoder(nn.Module):
    def __init__(self, in_channels, num_hiddens, num_residual_layers, num_residual_hiddens,
                 speaker_dic, speaker_embedding_dim, device,  verbose=False, debug=False):
        super(Decoder, self).__init__()
        self.verbose = verbose
        self.debug = debug
        self.device = device

        self._embedding = nn.Embedding(len(speaker_dic), speaker_embedding_dim)

        self._conv_1 = nn.Conv1d(in_channels=in_channels + speaker_embedding_dim,
                                 out_channels=num_hiddens,
                                 kernel_size=3,
                                 padding=1)

        self._upsample = nn.Upsample(scale_factor=2)

        self._residual_stack = ResidualStack(in_channels=num_hiddens,
                                             num_hiddens=num_hiddens,
                                             num_residual_layers=num_residual_layers,
                                             num_residual_hiddens=num_residual_hiddens)

        self._conv_trans_1 = nn.ConvTranspose1d(in_channels=num_hiddens,
                                                out_channels=num_hiddens,
                                                kernel_size=3,
                                                padding=1)

        self._conv_trans_2 = nn.ConvTranspose1d(in_channels=num_hiddens,
                                                out_channels=num_hiddens,
                                                kernel_size=3,
                                                padding=0)

        self._conv_trans_3 = nn.ConvTranspose1d(in_channels=num_hiddens,
                                                out_channels=1025,#1025, #257  # out_channels
                                                kernel_size=3,
                                                padding=3)

    def forward(self, inputs, speaker_dic, speaker_id):
        if self.debug:
            print('shape of inputs in Decoder.forward', inputs.size())
            sys.stdout.flush()

        lookup_tensor = torch.tensor([speaker_dic[str(int(i))] for i in speaker_id], dtype=torch.long).to(device)
        if self.debug:
            print(
                'shape of lookup_tensor in Decoder.forward',
                lookup_tensor.size())
            sys.stdout.flush()

        spk_emb = self._embedding(lookup_tensor)

        if self.debug:
            print('shape of spk_emb in Decoder.forward', spk_emb.size())
            sys.stdout.flush()
        spk_emb = spk_emb.unsqueeze(2)
        if self.debug:
            print("unqueezed spk_emb", spk_emb.size())
            sys.stdout.flush()
        spk_emb = spk_emb.repeat(1, 1, inputs.size(2))
        if self.debug:
            print("spk_emb repeated along time and batch ", spk_emb.size())
            sys.stdout.flush()

        x = torch.cat((spk_emb, inputs), dim=1)
        if self.debug:
            print('shape of x in Decoder.forward.cat', x.size())
            sys.stdout.flush()

        x = self._conv_1(x)
        if self.debug:
            print('shape of x in Decoder.forward._conv_1', x.size())
            sys.stdout.flush()

        x = self._upsample(x)
        if self.debug:
            print('shape of x in Decoder.forward._upsample', x.size())
            sys.stdout.flush()

        x = self._residual_stack(x)
        if self.debug:
            print('shape of x in Decoder.forward._residual_stack', x.size())
            sys.stdout.flush()

        x = self._conv_trans_1(x)
        if self.debug:
            print('shape of x in Decoder.forward._conv_trans_1', x.size())
            sys.stdout.flush()

        x = F.relu(x)  # self._conv_trans_1(x)
        if self.debug:
            print('shape of x in Decoder.forward._conv_trans_1', x.size())
            sys.stdout.flush()

        x = F.relu(self._conv_trans_2(x))
        if self.debug:
            print('shape of x in Decoder.forward._conv_trans_2', x.size())
            sys.stdout.flush()

        x = self._conv_trans_3(x)
        if self.debug:
            print('shape of x in Decoder.forward._conv_trans_3', x.size())
            sys.stdout.flush()

        return x
