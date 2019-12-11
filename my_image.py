def image_split(inp):
	return inp[:,:,0],inp[:,:,1],inp[:,:,2]

def remove_background(image_layer):
	threshold_back = 100
	image_layer[image_layer<threshold_back]=0
	return image_layer

def get_middle(x1,y1,x2,y2):
	return (x1+x2)*0.5,(y1+y2)*0.5


