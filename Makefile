all: blender2minecraft.zip

blender2minecraft.zip: $(shell find blender2minecraft -type f -not -name '.*')
	zip -r blender2minecraft.zip blender2minecraft/

install:
	unzip -o blender2minecraft.zip -d ~/.config/blender/2.78/scripts/addons

clean:
	rm blender2minecraft.zip
