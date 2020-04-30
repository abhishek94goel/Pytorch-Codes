# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 16:13:27 2020

@author: Abhishek Goel
"""

############### Lets built a GAN model using Pytorch ##################

import torch
import torch.nn as nn
import torch.nn.parallel
import torch.utils.data
import torchvision.datasets as dset
import torchvision.transforms as transforms
import torchvision.utils as vutils

# defining the Transformation hyperparameters
imageSize = 64
batchSize = 44

# defining the transform function
transform = transforms.Compose([transforms.Scale(imageSize), transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),])

# loading the CIFAR10 dataset
dataset = dset.CIFAR10(root='./data',train=True, transform=transform,download=True)
dataloader = torch.utils.data.DataLoader(dataset,batch_size=batchSize, shuffle=True)

num_batches = len(dataloader)

# Defining the weights_init function that takes as input a neural network m and that will initialize all its weights.
def weights_init(m):
  classname = m.__class__.__name__
  if classname.find('Conv') != -1:
    m.weight.data.normal_(0.0, 0.02)
  elif classname.find('BatchNorm') != -1:
    m.weight.data.normal_(1.0, 0.02)
    m.bias.data.fill_(0)
    
# Making the Generator of our GAN
class G(nn.Module):
  def __init__(self):
    super(G, self).__init__()
    self.main = nn.Sequential(
      nn.ConvTranspose2d(100, 512, 4, 1, 0, bias = False),
      nn.BatchNorm2d(512),
      nn.ReLU(True),
      nn.ConvTranspose2d(512, 256, 4, 2, 1, bias = False),
      nn.BatchNorm2d(256),
      nn.ReLU(True),
      nn.ConvTranspose2d(256, 128, 4, 2, 1, bias = False),
      nn.BatchNorm2d(128),
      nn.ReLU(True),
      nn.ConvTranspose2d(128, 64, 4, 2, 1, bias = False),
      nn.BatchNorm2d(64),
      nn.ReLU(True),
      nn.ConvTranspose2d(64, 3, 4, 2, 1, bias = False),
      nn.Tanh()
        )  
    
  def forward(self, input):
    output = self.main(input)
    return output


# Making the Descriminator
class D(nn.Module):
  def __init__(self): # We introduce the __init__() function that will define the architecture of the discriminator.
        super(D, self).__init__() # We inherit from the nn.Module tools.
        self.main = nn.Sequential( # We create a meta module of a neural network that will contain a sequence of modules (convolutions, full connections, etc.).
            nn.Conv2d(3, 64, 4, 2, 1, bias = False), # We start with a convolution.
            nn.LeakyReLU(0.2, inplace = True), # We apply a LeakyReLU.
            nn.Conv2d(64, 128, 4, 2, 1, bias = False), # We add another convolution.
            nn.BatchNorm2d(128), # We normalize all the features along the dimension of the batch.
            nn.LeakyReLU(0.2, inplace = True), # We apply another LeakyReLU.
            nn.Conv2d(128, 256, 4, 2, 1, bias = False), # We add another convolution.
            nn.BatchNorm2d(256), # We normalize again.
            nn.LeakyReLU(0.2, inplace = True), # We apply another LeakyReLU.
            nn.Conv2d(256, 512, 4, 2, 1, bias = False), # We add another convolution.
            nn.BatchNorm2d(512), # We normalize again.
            nn.LeakyReLU(0.2, inplace = True), # We apply another LeakyReLU.
            nn.Conv2d(512, 1, 4, 1, 0, bias = False), # We add another convolution.
            nn.Sigmoid() # We apply a Sigmoid rectification to break the linearity and stay between 0 and 1.
        )
    
  def forward(self,input):
    output = self.main(input)
    return output.view(-1)  # for flatenning of Single channel images of the batch
  
# Initializing the objects of Generator and Descriminator
# also Initializing their weights
netG = G()
netG.apply(weights_init)
netD = D()
netD.apply(weights_init)

## Initializing the Loss functions and Optimizers
criterion = nn.BCELoss()
optimizerG = torch.optim.Adam(netG.parameters(), lr=0.002, betas=(0.5, 0.999))
optimizerD = torch.optim.Adam(netD.parameters(), lr=0.002, betas=(0.5, 0.999))


### Final Training of Our GAN ###

for epoch in range(25):
  for i, data in enumerate(dataloader, 0):
    
    #################### Training of the Descriminator #########################
    
    netD.zero_grad()
    real_image = data[0]
    batch_size = real_image.size()[0]
    
    # Training the discriminator with a real image of the dataset #
    target = torch.ones(batch_size)
    # Forward Pass
    output = netD.forward(real_image)
    errD_real = criterion(output, target)
  
    # Training the discriminator with a fake image generated by the generator
    noise = torch.randn(batch_size, 100, 1, 1)
    #forward pass in Generator to develop the fake image
    fake = netG.forward(noise)
    target = torch.zeros(batch_size)
    #forward pass of Fake images in Descriminator
    output = netD.forward(fake.detach())
    errD_fake = criterion(output, target)
    
    # Backpropagating the total error
    errD = errD_real + errD_fake
    errD.backward() # Calculation of gradients
    optimizerD.step()

    
    #################### Training of the Generator ################################
    
    netG.zero_grad()
    
    target = torch.ones(batch_size)
    output = netD(fake)
    errG = criterion(output, target)
    errG.backward()
    optimizerG.step()
    
        
    #################### Printing the losses and saving the real images and the generated images of the minibatch every 100 steps ######################

    print(f"Epoch- [{epoch}/{25}]. Batch_num- [{i}/{num_batches}]. Loss_D: {errD.data}. Loss_G: {errG.data}")
    if i % 100 == 0: # Every 100 steps of batch:
      vutils.save_image(real_image, '%s/real_samples.png' % "./results", normalize = True)
      fake = netG.forward(noise)
      vutils.save_image(fake.data, '%s/fake_samples_epoch_%03d.png' % ("./results", epoch), normalize = True)