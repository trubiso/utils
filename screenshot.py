#! /usr/sbin/python
import os

base = "/mnt/data/Imágenes/Capturas de pantalla"

os.system("flameshot gui")

for file in os.listdir(base + "/unsorted"):
	dir = file[:len("20XX-XX")]
	# make the directory if it does not exist
	try:
		os.mkdir(f"{base}/{dir}")
	finally:
		os.rename(f"{base}/unsorted/{file}", f"{base}/{dir}/{file}")
