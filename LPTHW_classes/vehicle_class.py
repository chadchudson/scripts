#!/usr/bin/python

class Vehicle(object):

	def __init__(self, make):
		self.make = make

	def print_make(self):
		for shit in self.make:
			print shit

truck = Vehicle(["Chevrolet"])

suv = Vehicle(["Ferrari"])

roller_coaster = Vehicle(["Interesting"])

truck.print_make()

suv.print_make()

roller_coaster.print_make()
