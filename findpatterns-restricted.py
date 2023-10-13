'''
Chrysanthi Kosyfaki
'''

# code for restricted patterns
# restricted means that origins can take atomic regions from a restricted domain (e.g. south Manhattan) 
# instead of taking values from the entire map
# same holds for destinations and timeslots

import sys
import time


if len(sys.argv)!=7:
	print('Usage: python3 patterns <region_graph> <trips_graph> <support for atomic patterns> <support for extended patterns> <timebound> <restrictions_file>')
	exit()

# open trips file and compute atomic patterns

f_restrictions = open(sys.argv[6])
l = f_restrictions.readline()
restricted_origin = set(int(x) for x in l.split())
print(restricted_origin)
l = f_restrictions.readline()
restricted_dest = set(int(x) for x in l.split())
print(restricted_dest)
l = f_restrictions.readline().split()
time_start = int(l[0])
time_end = int(l[1])
print(time_start,time_end)
f_restrictions.close()

f = open(sys.argv[2])

atomic = {}
flows = []
for l in f:
	l = [int(x) for x in l.split()]
	if l[0]==l[1]: continue
	if l[0] not in restricted_origin or l[1] not in restricted_dest or l[2]<time_start or l[2]>time_end: 
		continue # skip flows outside restricted regions/times
	flows.append(l[3]) # keep track of all flows, to find the top-k
	if l[0] in atomic: # source already seen before
		if l[1] in atomic[l[0]]: # dest already seen before
			atomic[l[0]][l[1]][l[2]] = l[3] # record timeslot + flow
			#print ("kery = ",l[0]," ",l[1], " ",l[2],"\tvalue = ", atomic[l[0]][l[1]][l[2]])
		else: # dest not seen before for this source
			atomic[l[0]][l[1]] = {l[2]:l[3]}
		#print("here")
	else: # source not seen before
		atomic[l[0]] = {l[1]:{l[2]:l[3]}}

#exit()
numatomic = len(flows)
supatomic = float(sys.argv[3])
minratio = float(sys.argv[4])
supatomicnumber = sorted(flows, reverse=True)[int(supatomic*numatomic)]
print('number of atomic:',numatomic)
print('supatomicnumber:',supatomicnumber)
#exit()
timebound = int(sys.argv[5])-1

#for i in atomic:
#	for j in atomic[i]:
#		for k in atomic[i][j]:
#			if atomic[i][j][k]>=supatomicnumber:
#				print(i,j,k,atomic[i][j][k])
		
# load neighborhood graph from file
f = open(sys.argv[1])

# create two neighborhood graphs, one for O and one for D based on restrictions
neighborO = {}
neighborD = {}
for l in f:
	l = [int(x) for x in l.split()]
	#print ("l  = ",l )
	if l[0]==l[1]: continue
	if l[0] in restricted_origin and l[1] in restricted_origin:
		if l[0] in neighborO: # source already seen before
			neighborO[l[0]].append(l[1])
		else: # source not seen before
			neighborO[l[0]]=[l[1]]
	if l[1] in restricted_dest and l[1] in restricted_dest:
		if l[0] in neighborD: # dest already seen before
			neighborD[l[0]].append(l[1])
		else: # dest not seen before
			neighborD[l[0]]=[l[1]]

def baseline():
	patterns = [{},{},{},{}]
	
	for i in atomic:
		for j in atomic[i]:
			for k in atomic[i][j]:
				if atomic[i][j][k]>=supatomicnumber:
					patterns[3][(tuple([i]),tuple([j]),tuple([k]))]=1 # set support count of atomic triple to 1
			
	print('number of atomic patterns:',len(patterns[3]))
					
	size = 4
	while patterns[size-1]:
		patterns.append({})
		
		# try all minimal generalizations
		for p in patterns[size-1]:
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])
			# try to expand source
			for src in p[0]:
				if src in neighborO:
					for n in neighborO[src]:
						expsrc = tuple(sorted(list((p[0]+(n,)))))
						if (expsrc,p[1],p[2]) in patterns[size]: continue # already found this pattern before
						cursupcount = patterns[size-1][p]
						if n in atomic and n not in p[0] and n not in p[1]:
							# examine all atomic patterns that consist of src and all combinations
							# of dest and time in patterns[size-1][p]
							for j in p[1]: # for each dest in p
								if j in atomic[n]:
									for k in p[2]: # for each timeslot in p
										if k in atomic[n][j]:
											if atomic[n][j][k]>=supatomicnumber:
												cursupcount+=1
							if cursupcount>=(len(p[0])+1)*len(p[1])*len(p[2])*minratio:
								patterns[size][(expsrc,p[1],p[2])]=cursupcount
			# try to expand dest
			for dest in p[1]:
				if dest in neighborD:
					for n in neighborD[dest]:
						expdest = tuple(sorted(list((p[1]+(n,)))))
						if (p[0],expdest,p[2]) in patterns[size]: continue # already found this pattern before
						cursupcount = patterns[size-1][p]
						if n not in p[0] and n not in p[1]:
							# examine all atomic patterns that consist of src and all combinations
							# of dest and time in patterns[size-1][p]
							for i in p[0]: # for each src in p
								if i in atomic:
									for k in p[2]: # for each timeslot in p
										if n in atomic[i] and k in atomic[i][n]:
											if atomic[i][n][k]>=supatomicnumber:
												cursupcount+=1
							if cursupcount>=len(p[0])*(1+len(p[1]))*len(p[2])*minratio:
								patterns[size][(p[0],expdest,p[2])]=cursupcount
			# try to expand timeslot (forward expansion, since backward expansion should be handled by another pattern)
			nextts = p[2][-1]+1
			if nextts <= time_end and nextts-p[2][0]<=timebound:
				cursupcount = patterns[size-1][p]
				for i in p[0]: # for each src in p
					if i in atomic:
						for j in p[1]: # for each dest in p
							if j in atomic[i]:
								if nextts in atomic[i][j] and atomic[i][j][nextts]>=supatomicnumber:
									cursupcount+=1
				if cursupcount>=len(p[0])*len(p[1])*(1+len(p[2]))*minratio:
						patterns[size][(p[0],p[1],p[2]+(nextts,))]=cursupcount
			prevts = p[2][0]-1
			if prevts >= time_start and p[2][-1]-prevts<=timebound:
				expts = (prevts,)+p[2]
				if (p[0],p[1],expts) in patterns[size]: continue # already found this pattern before
				cursupcount = patterns[size-1][p]
				for i in p[0]: # for each src in p
					if i in atomic:
						for j in p[1]: # for each dest in p
							if j in atomic[i]:
								if prevts in atomic[i][j] and atomic[i][j][prevts]>=supatomicnumber:
									cursupcount+=1
				if cursupcount>=len(p[0])*len(p[1])*(1+len(p[2]))*minratio:
						patterns[size][(p[0],p[1],expts)]=cursupcount
		#patterns.append([])
		sortedpatterns = list(patterns[size].items())
		sortedpatterns.sort(key = lambda x: (x[1],x[0]), reverse=True)
		if len(sortedpatterns)>0:
			print(sortedpatterns[:5])
			print("############")
		
		size += 1
		#if size == 10: break
		
		
		
	for s in range(3,size):
	  	print('size:',s)
	  	print('number of patterns:',len(patterns[s]))
	#  	print(patterns[s])
	#print('total number of patterns:',sum([len(patterns[s]) for s in range(3,size)]))
	return patterns

def get_neighbors(region, other, neighbor):
	neighbors = []
	for l in region:
		if l in neighbor:
			neighbors.extend(neighbor[l])
	neighbors = set(neighbors)
	neighbors.difference_update(region)
	neighbors.difference_update(other)
	return neighbors
	

# extends improved5 with the neighbor implementation of improved7
def AVFCIN():
	triples = [{},{},{},{}] # records counted ODT triples
	patterns = [{},{},{},{}] # records counted ODT triples which are patterns (they satisfy minratio)
	dests = {} # records dests with non-zero atomic score for each src
	sources = {} # records sources with non-zero atomic score for each dest

	for i in atomic:
		for j in atomic[i]:
			for k in atomic[i][j]:
				if atomic[i][j][k]>=supatomicnumber:
					patterns[3][(tuple([i]),tuple([j]),tuple([k]))]=1 # set support count of atomic triple to 1
					if i in dests: dests[i].add(j)
					else: dests[i]=set([j])
					if j in sources: sources[j].add(i)
					else: sources[j]=set([i])
	
	# comment this block (for debugging and statistics only)
# 	for i in range(5):
# 		if i in dests:
# 			print(i,": destinations = ",dests[i])
# 		if i in sources:
# 			print(i,": sources = ",sources[i])
						
	triples[3] = patterns[3]		
	#print('number of atomic patterns:',len(patterns[3]))
		
	size = 4
	#numsavings = [0,0,0,0] # how many pprime we avoided counting
	#numfullcomp = [0,0,0,0] # how many pprime we fully counted
	#numgen = [0,0,0,0] # how many candidate ODT triples we generated
	while patterns[size-1]:
		patterns.append({})
		triples.append({})
		#numsavings.append(0)
		#numfullcomp.append(0)
		#numgen.append(0)

		# try all minimal generalizations
		for p in patterns[size-1]:
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])

			startingsupport = patterns[size-1][p]

			# try to expand source
			neigh = get_neighbors(p[0],p[1],neighborO)
			for n in neigh:
#			for n in next_neighbor(p[0],p[1]):
				# if n in p[0] or n in p[1]: continue

				expsrc = tuple(sorted(list((p[0]+(n,)))))
				if (expsrc,p[1],p[2]) in triples[size]: continue # already examined this pattern before
				cursupcount = startingsupport

				#check if OD pair of pprime has at support at least one
				if n not in dests or not dests[n]&set(p[1]): # no chance to find any atomic pattern in pprime
					if n in atomic :
						if cursupcount>=(len(p[0])+1)*len(p[1])*len(p[2])*minratio:
							patterns[size][(expsrc,p[1],p[2])]=cursupcount
						triples[size][(expsrc,p[1],p[2])]=cursupcount
				else:
					if n in atomic :
						pprime = ((n,),p[1],p[2])
						if pprime in triples[1+len(p[1])+len(p[2])]: # pprime already counted
							cursupcount+= triples[1+len(p[1])+len(p[2])][pprime]
							#numsavings[size] +=1
						else:
							#numfullcomp[size]+=1
							# examine all atomic patterns that consist of src and all combinations
							# of dest and time in patterns[size-1][p]
							for j in p[1]: # for each dest in p
								if j in atomic[n]:
									for k in p[2]: # for each timeslot in p
										if k in atomic[n][j]:
											if atomic[n][j][k]>=supatomicnumber:
												cursupcount+=1
							#if patterns[size-1][p]<cursupcount: # support increased
							#	odpairs.add(((n,),p[1]))
							#	odpairs.add((expsrc,p[1]))
						if cursupcount>=(len(p[0])+1)*len(p[1])*len(p[2])*minratio:
							patterns[size][(expsrc,p[1],p[2])]=cursupcount
						triples[size][(expsrc,p[1],p[2])]=cursupcount

			# try to expand dest
			neigh = get_neighbors(p[1],p[0],neighborD)
			for n in neigh:
#			for n in next_neighbor(p[1],p[0]):
				# if n in p[0] or n in p[1]: continue
				expdest = tuple(sorted(list((p[1]+(n,)))))
				if (p[0],expdest,p[2]) in triples[size]: continue # already examined this pattern before
				cursupcount = startingsupport
	
				#check if OD pair of pprime has at support at least one
				if n not in sources or not sources[n]&set(p[0]): # no chance to find any atomic pattern in pprime
				#if (p[0],(n,)) not in odpairs: # no chance to find any atomic pattern in pprime
					#numsavings[size] +=1
					 #print('diff triple',pprime,'guaranteed to have 0 count')
					if cursupcount>=len(p[0])*(1+len(p[1]))*len(p[2])*minratio:
						patterns[size][(p[0],expdest,p[2])]=cursupcount
					triples[size][(p[0],expdest,p[2])]=cursupcount
				else:
					pprime = (p[0],(n,),p[2])
					if pprime in triples[len(p[0])+1+len(p[2])]:
						cursupcount+= triples[len(p[0])+1+len(p[2])][pprime]
						#numsavings[size] +=1
					else:
						#numfullcomp[size]+=1
						# examine all atomic patterns that consist of src and all combinations
						# of dest and time in patterns[size-1][p]
						for i in p[0]: # for each src in p
							if i in atomic:
								for k in p[2]: # for each timeslot in p
									if n in atomic[i] and k in atomic[i][n]:
										if atomic[i][n][k]>=supatomicnumber:
											cursupcount+=1
						#if patterns[size-1][p]<cursupcount: # support increased
						#	odpairs.add((p[0],(n,)))
						#	odpairs.add((p[0],expdest))
					if cursupcount>=len(p[0])*(1+len(p[1]))*len(p[2])*minratio:
						patterns[size][(p[0],expdest,p[2])]=cursupcount
					triples[size][(p[0],expdest,p[2])]=cursupcount

						#odpairs.add((p[0],expdest))
			# try to expand timeslot (forward expansion)
			nextts = p[2][-1]+1
#			if nextts <= 47:
			if nextts <= time_end and nextts-p[2][0]<=timebound:
				#numgen[size]+=1
				cursupcount = startingsupport
				pprime = (p[0],p[1],(nextts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
					#numsavings[size] +=1
				else:
					#numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if nextts in atomic[i][j] and atomic[i][j][nextts]>=supatomicnumber:
										cursupcount+=1
				if cursupcount>=len(p[0])*len(p[1])*(1+len(p[2]))*minratio:
					patterns[size][(p[0],p[1],p[2]+(nextts,))]=cursupcount
				triples[size][(p[0],p[1],p[2]+(nextts,))]=cursupcount
			prevts = p[2][0]-1 # try backward expansion
			if prevts >= time_start and p[2][-1]-prevts<=timebound:
				#numgen[size]+=1
				expts = (prevts,)+p[2]
				if (p[0],p[1],expts) in triples[size]: continue # already examined this pattern before
				cursupcount = startingsupport
				pprime = (p[0],p[1],(prevts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
					#numsavings[size] +=1
				else:
					#numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if prevts in atomic[i][j] and atomic[i][j][prevts]>=supatomicnumber:
										cursupcount+=1
				if cursupcount>=len(p[0])*len(p[1])*(1+len(p[2]))*minratio:
					patterns[size][(p[0],p[1],expts)]=cursupcount
				triples[size][(p[0],p[1],expts)]=cursupcount
		#patterns.append([])
		size += 1

	return patterns

# improved_prefix_time with restricted origin/dest/time
def OPT():
	atomicset = set()
	triples = [{},{},{},{}] # records counted ODT triples
	patterns = [{},{},{},{}] # records counted ODT triples which are patterns (they satisfy minratio)
	dests = {} # records dests with non-zero atomic score for each src
	sources = {} # records sources with non-zero atomic score for each dest
	timeprefsums = {} # for each atomic origin-dest pair, a 1D prefix sum array with the sum of atomic patterns 

#	measuredtime = 0.0

	wastedexp1 = 0 # wasted expansions because triple considered before
	wastedexp2 = 0 # wasted expansions because triple considered before
	wastedexp3 = 0 # wasted expansions because triple considered before

#	st = time.time()
	for i in atomic:
		for j in atomic[i]:
			cursum =0
			timeprefsums[(i,j)]=[0] # holds prefix sum for all timeslots in o=i and d=j
			for k in range(48): # for all timeslots
				if k in atomic[i][j] and atomic[i][j][k]>=supatomicnumber:
					patterns[3][(tuple([i]),tuple([j]),tuple([k]))]=1 # set support count of atomic triple to 1
					if i in dests: dests[i].add(j)
					else: dests[i]=set([j])
					if j in sources: sources[j].add(i)
					else: sources[j]=set([i])
					cursum+=1
				timeprefsums[(i,j)].append(cursum)
						
	triples[3] = patterns[3]		
	#print('number of atomic patterns:',len(patterns[3]))
		
	size = 4
	#numsavings = [0,0,0,0] # how many pprime we avoided counting
	#numfullcomp = [0,0,0,0] # how many pprime we fully counted
	#numgen = [0,0,0,0] # how many candidate ODT triples we generated
	while patterns[size-1]:
		

		#print('Number of patterns at level',size-1,'=',len(patterns[size-1]))
		patterns.append({})
		triples.append({})
		#numsavings.append(0)
		#numfullcomp.append(0)
		#numgen.append(0)

		# try all minimal generalizations
		for p in patterns[size-1]:
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])

			startingsupport = patterns[size-1][p]

			# try to expand source
			neigh = get_neighbors(p[0],p[1],neighborO)
			for n in neigh:
#			for n in next_neighbor(p[0],p[1]):
				# if n in p[0] or n in p[1]: continue

				#numgen[size]+=1
				# expsrc = tuple(sorted(list((p[0]+(n,)))))
				expsrc = tuple(sorted((p[0]+(n,))))
				if (expsrc,p[1],p[2]) in triples[size]: 
					# wastedexp1 +=1	
					continue # already examined this pattern before
				cursupcount = startingsupport
				
				
				#check if OD pair of pprime has at support at least one
				if n not in dests or not dests[n]&set(p[1]): # no chance to find any atomic pattern in pprime
#							if ((n,),p[1]) not in odpairs: # no chance to find any atomic pattern in pprime
					if n in atomic:
						if cursupcount>=(len(p[0])+1)*len(p[1])*len(p[2])*minratio:
							patterns[size][(expsrc,p[1],p[2])]=cursupcount
						triples[size][(expsrc,p[1],p[2])]=cursupcount
					#numsavings[size] +=1
					# print('diff triple',pprime,'guaranteed to have 0 count')
				else:
					if n in atomic:
						pprime = ((n,),p[1],p[2])
						if pprime in triples[1+len(p[1])+len(p[2])]: # pprime already counted
							cursupcount+= triples[1+len(p[1])+len(p[2])][pprime]
							#numsavings[size] +=1
						else:
							
							#numfullcomp[size]+=1
							# examine all atomic patterns that consist of src and all combinations
							# of dest and time in patterns[size-1][p]
							for j in p[1]: # for each dest in p
								if j in atomic[n]:
									cursupcount+=timeprefsums[(n,j)][p[2][-1]+1]-timeprefsums[(n,j)][p[2][0]]
									#for k in p[2]: # for each timeslot in p
									#	if k in atomic[n][j]:
									#		if atomic[n][j][k]>=supatomicnumber:
									#			cursupcount+=1
							#if patterns[size-1][p]<cursupcount: # support increased
							#	odpairs.add(((n,),p[1]))
							#	odpairs.add((expsrc,p[1]))
						if cursupcount>=(len(p[0])+1)*len(p[1])*len(p[2])*minratio:
							patterns[size][(expsrc,p[1],p[2])]=cursupcount
						triples[size][(expsrc,p[1],p[2])]=cursupcount
						#odpairs.add((expsrc,p[1]))


			# try to expand dest
#			st = time.time()
			neighs = get_neighbors(p[1],p[0],neighborD)
			for n in neighs:
			# for n in next_neighbor(p[1],p[0]):
				# if n in p[0] or n in p[1]: continue
				#numgen[size]+=1
				# expdest = tuple(sorted(list((p[1]+(n,)))))
				expdest = tuple(sorted((p[1]+(n,))))
				if (p[0],expdest,p[2]) in triples[size]: 
					# wastedexp2 +=1	
					continue # already examined this pattern before

				cursupcount = startingsupport
				#check if OD pair of pprime has at support at least one
				if n not in sources or not sources[n]&set(p[0]): # no chance to find any atomic pattern in pprime
				#if (p[0],(n,)) not in odpairs: # no chance to find any atomic pattern in pprime
					#numsavings[size] +=1
					# print('diff triple',pprime,'guaranteed to have 0 count')
					if cursupcount>=len(p[0])*(1+len(p[1]))*len(p[2])*minratio:
						patterns[size][(p[0],expdest,p[2])]=cursupcount
					triples[size][(p[0],expdest,p[2])]=cursupcount
				else:
					pprime = (p[0],(n,),p[2])
					if pprime in triples[len(p[0])+1+len(p[2])]:
						cursupcount+= triples[len(p[0])+1+len(p[2])][pprime]
						#numsavings[size] +=1
					else:						
						#numfullcomp[size]+=1
						# examine all atomic patterns that consist of src and all combinations
						# of dest and time in patterns[size-1][p]
						for i in p[0]: # for each src in p
							if i in atomic and n in atomic[i]:
								cursupcount+=timeprefsums[(i,n)][p[2][-1]+1]-timeprefsums[(i,n)][p[2][0]]
								#for k in p[2]: # for each timeslot in p
								#	if n in atomic[i] and k in atomic[i][n]:
								#		if atomic[i][n][k]>=supatomicnumber:
								#			cursupcount+=1
						#if patterns[size-1][p]<cursupcount: # support increased
						#	odpairs.add((p[0],(n,)))
						#	odpairs.add((p[0],expdest))
						
					if cursupcount>=len(p[0])*(1+len(p[1]))*len(p[2])*minratio:
						patterns[size][(p[0],expdest,p[2])]=cursupcount
					triples[size][(p[0],expdest,p[2])]=cursupcount
					#odpairs.add((p[0],expdest))
			# et = time.time()
			# measuredtime += et-st	

			# try to expand timeslot (forward expansion)
			nextts = p[2][-1]+1
#			if nextts <= 47:
			if nextts <= time_end and nextts-p[2][0]<=timebound:
				#numgen[size]+=1
				cursupcount = startingsupport
				pprime = (p[0],p[1],(nextts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
					#numsavings[size] +=1
				else:
					#numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if nextts in atomic[i][j] and atomic[i][j][nextts]>=supatomicnumber:
										cursupcount+=1
				if cursupcount>=len(p[0])*len(p[1])*(1+len(p[2]))*minratio:
					patterns[size][(p[0],p[1],p[2]+(nextts,))]=cursupcount
				triples[size][(p[0],p[1],p[2]+(nextts,))]=cursupcount
			prevts = p[2][0]-1 # try backward expansion
			if prevts >= time_start and p[2][-1]-prevts<=timebound:
				#numgen[size]+=1
				expts = (prevts,)+p[2]
				if (p[0],p[1],expts) in triples[size]: 
					# wastedexp3 +=1	
					continue # already examined this pattern before
				cursupcount = startingsupport
				pprime = (p[0],p[1],(prevts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
					#numsavings[size] +=1
				else:
					#numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if prevts in atomic[i][j] and atomic[i][j][prevts]>=supatomicnumber:
										cursupcount+=1
				if cursupcount>=len(p[0])*len(p[1])*(1+len(p[2]))*minratio:
					patterns[size][(p[0],p[1],expts)]=cursupcount
				triples[size][(p[0],p[1],expts)]=cursupcount
			

		#patterns.append([])
		size += 1

	return patterns


print('\nbaseline is running:\n')
st = time.time()
patterns = baseline()	
et = time.time()
elapsed_time = et - st
print('Execution time of baseline:', elapsed_time, 'seconds')

print('total number of patterns:',sum([len(patterns[s]) for s in range(len(patterns))]))
#for s in range(3,len(patterns)):
#	print('size:',s,'\tnumber of patterns:',len(patterns[s]))

print('\nAVFCIN is running:\n')
st = time.time()
patterns = AVFCIN()
et = time.time()
elapsed_time = et - st
print('Execution time of AVFCIN:', elapsed_time, 'seconds')

print('total number of patterns:',sum([len(patterns[s]) for s in range(len(patterns))]))
#for s in range(3,len(patterns)):
#	print('size:',s,'\tnumber of patterns:',len(patterns[s]))
#print('\n#########################################\n')


print('\nOPT is running:\n')
st = time.time()
patterns = OPT()
et = time.time()
elapsed_time = et - st
print('Execution time of OPT:', elapsed_time, 'seconds')

print('total number of patterns:',sum([len(patterns[s]) for s in range(len(patterns))]))
#for s in range(3,len(patterns)):
#	print('size:',s,'\tnumber of patterns:',len(patterns[s]))
#print('\n#########################################\n')
