'''
Chrysanthi Kosyfaki
'''
# code for bounded patterns
# bounded means that the size of an extended origin cannot be more than a maximum number of regions
# e.g. the origin O of a pattern cannot grow to include more than 5 atomic regions
# same bounding constraints can be put for extended destinations and timeslots

import sys
import time


if len(sys.argv)!=8:
	print('Usage: python3 patterns <region_graph> <trips_graph> <support for atomic patterns> <support for extended patterns> <timebound> <originbound> <destbound>')
	exit()

f = open(sys.argv[2])

atomic = {}
flows = []
for l in f:
	l = [int(x) for x in l.split()]
	if l[0]==l[1]: continue
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
originbound = int(sys.argv[6])
destbound = int(sys.argv[7])

#for i in atomic:
#	for j in atomic[i]:
#		for k in atomic[i][j]:
#			if atomic[i][j][k]>=supatomicnumber:
#				print(i,j,k,atomic[i][j][k])
		
# load neighborhood graph from file
f = open(sys.argv[1])

neighbor = {}
for l in f:
	l = [int(x) for x in l.split()]
	#print ("l  = ",l )
	if l[0]==l[1]: continue
	if l[0] in neighbor: # source already seen before
		neighbor[l[0]].append(l[1])
	else: # source not seen before
		neighbor[l[0]]=[l[1]]
	if l[1] in neighbor: # dest already seen before
		neighbor[l[1]].append(l[0])
	else: # dest not seen before
		neighbor[l[1]]=[l[0]]

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
			# try to expand origin
			if len(p[0])<originbound: # origin expanded only if bound is not reached
				for src in p[0]:
					if src in neighbor:
						for n in neighbor[src]:
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
			if len(p[1])<destbound: # dest expanded only if bound is not reached
				for dest in p[1]:
					if dest in neighbor:
						for n in neighbor[dest]:
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
			if nextts <= 47 and nextts-p[2][0]<=timebound:
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
			if prevts >= 0 and p[2][-1]-prevts<=timebound:
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
		size += 1
		#if size == 10: break

	for s in range(3,size):
		print('size:',s)
		print('number of patterns:',len(patterns[s]))
		#print(patterns[s])
	#print('total number of patterns:',sum([len(patterns[s]) for s in range(3,size)]))
	return patterns

def get_neighbors(region, other):
	neighbors = []
	for l in region:
		if l in neighbor:
			neighbors.extend(neighbor[l])
	neighbors = set(neighbors)
	neighbors.difference_update(region)
	neighbors.difference_update(other)
	return neighbors
	
def AVFCIN():
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


		# try all minimal generalizations
		for p in patterns[size-1]:
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])

			startingsupport = patterns[size-1][p]

			# try to expand source
			if len(p[0])<originbound:
				neigh = get_neighbors(p[0],p[1])
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
			if len(p[1])<destbound:
    #			st = time.time()
				neighs = get_neighbors(p[1],p[0])
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
			if nextts <= 47 and nextts-p[2][0]<=timebound:
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
			if prevts >= 0 and p[2][-1]-prevts<=timebound:
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
			
		size += 1
	return patterns


def OPT():
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
							
	triples[3] = patterns[3]		
	#print('number of atomic patterns:',len(patterns[3]))
		
	size = 4
	while patterns[size-1]:
		patterns.append({})
		triples.append({})

		# try all minimal generalizations
		for p in patterns[size-1]:
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])

			startingsupport = patterns[size-1][p]

			# try to expand source
			if len(p[0])<originbound:
				neigh = get_neighbors(p[0],p[1])
				for n in neigh:
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
			if len(p[1])<destbound:
				neigh = get_neighbors(p[1],p[0])
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

			# try to expand timeslot (forward expansion)
			nextts = p[2][-1]+1
#			if nextts <= 47:
			if nextts <= 47 and nextts-p[2][0]<=timebound:
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
			if prevts >= 0 and p[2][-1]-prevts<=timebound:
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

print('\nbaseline is running:\n')
st = time.time()
patterns = baseline()	
et = time.time()
elapsed_time = et - st
print('Execution time of baseline:', elapsed_time, 'seconds')

print('total number of patterns:',sum([len(patterns[s]) for s in range(len(patterns))]))




print('\nAVFCIN is running:\n')
st = time.time()
patterns = AVFCIN()
et = time.time()
elapsed_time = et - st
print('Execution time of AVFCIN:', elapsed_time, 'seconds')

print('total number of patterns:',sum([len(patterns[s]) for s in range(len(patterns))]))



print('\nOPT is running:\n')
st = time.time()
patterns = OPT()
et = time.time()
elapsed_time = et - st
print('Execution time of OPT:', elapsed_time, 'seconds')

print('total number of patterns:',sum([len(patterns[s]) for s in range(len(patterns))]))

