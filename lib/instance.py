from util import *

class Instance:

	def __init__(self, coord, datum):
		self.coord = coord
		self.datum = datum

	def Coord(self):
                return [self.coord.x, self.coord.y, self.klass()]
	
	def klass(self):
		return self.datum[-1]
	
class InstanceCollection:
	
	def __init__(self, data_collection):
                self.instances = []
                self.max_x = 0
                self.max_y = 0
		east, west = data_collection.find_poles()
		base_d = distance(east, west)

		for datum in data_collection.datums:
			a = distance(west, datum)
			b = distance(east, datum)
			x = (b**2 - base_d**2 - a**2) / (-2 * base_d)
			if x > self.max_x:
				self.max_x = x
			try:
                                y = math.sqrt(a**2 - x**2)
                        except ValueError:
                                y = 0
			if y > self.max_y:
				self.max_y = y
			self.instances.append(Instance(DataCoordinate(x,y), datum))

	def normalize_coordinates(self):
		for instance in self.instances:
			instance.coord.x = instance.coord.x / self.max_x
			instance.coord.y = instance.coord.y / self.max_y
	
	def log_x_coordinates(self):
		for instance in self.instances:
			instance.coord.x = math.log(instance.coord.x + 0.0001)

	def log_y_coordinates(self):
		for instance in self.instances:
			instance.coord.y = math.log(instance.coord.y + 0.0001)

	def klasses(self):
		return [ inst.klass for inst in self.instances ]
	
	def coords(self):
		return [ inst.coord for inst in self.instances ]

	def datums(self):
		return [ inst.datum for inst in self.instances ]


	def k_fold_stratified_cross_val(self, k=10):
		bins = []
		bin_count = []
		random.shuffle(self.instances,random.random)
		if not isnumeric(self.instances[0].klass()):
			data = sort_by_class(self.instances)
		for i in range(k):
			bins.append([])
			bin_count.append(0)
		for instance in self.instances:
			try:
				index = bin_count.index(0)
				bins[index].append(instance)
				bin_count[index] = 1
			except:
				for i in range(k):
					bin_count[i]=0
				index = bin_count.index(0)
				bins[index].append(instance)
				bin_count[index] = 1
		return bins

	def stratified_cross_val(self, option):
		random.shuffle(self.instances, random.random)
		if not isnumeric(self.instances[0].klass()):
			data = sort_by_class(self.instances)
		train_count = 0
		test_count = 0
		train = []
		test = []
		for instance in self.instances:
			if train_count < option[0]:
				train_count = train_count + 1
				train.append(instance)
			elif test_count < option[1]:
				test_count = test_count + 1
				test.append(instance)
				if train_count == option[0] and test_count == option[1]:
					train_count = 0
					test_count = 0
		return train, test

	def two_bins(self):
		random.shuffle(self.instances, random.random)
		g1 = self.instances[0:len(self.instances)/2]
		g2 = self.instances[(len(self.instances)/2)+1:-1]
		return g1, g2

	def shuffle(self):
		random.shuffle(self.instances, random.random)

class DataCoordinate:
	def __init__(self, x, y):
		self.x = x
		self.y = y
	
class DataCollection:
	def __init__(self, datums):
		self.datums = datums
	
	def add_datum(self, datum):
		datums.append(datum)

	def find_poles(self):
		this = random_element(self.datums)
		self.datums.remove(this)
		east = farthest_from(this, self.datums)
		self.datums.remove(east)
		self.datums.append(this)
		west = farthest_from(east, self.datums)
		self.datums.append(east)
		self.datums.append(west)
		return east, west
