import sys
import time
import math
import heapq

# based on atomic pattern ratio, not on flow
# selects, at each level the top k patterns
# we need an algebraic way to measure the number of minimal generalizations at each level
def baseline(K):
	patterns = [{},{},{},{}]
	
# 	st = time.time()
	for i in atomic:
		for j in atomic[i]:
			for k in atomic[i][j]:
				if atomic[i][j][k]>=supatomicnumber:
					patterns[3][(tuple([i]),tuple([j]),tuple([k]))]=1 # set support count of atomic triple to 1
			
	print('number of atomic patterns:',len(patterns[3]))

	size = 4
	while patterns[size-1] and size<=maxLevel:
		patterns.append({})
		
		# try all minimal generalizations
		for p in patterns[size-1]:
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])
			# try to expand source
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
						patterns[size][(expsrc,p[1],p[2])]=cursupcount
			# try to expand dest
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
						patterns[size][(p[0],expdest,p[2])]=cursupcount
			# try to expand timeslot (forward expansion, since backward expansion should be handled by another pattern)
			nextts = p[2][-1]+1
			if nextts <= 47 and nextts-p[2][0]<=timebound:
				expts = p[2]+(nextts,)
				if (p[0],p[1],expts) in patterns[size]: continue # already found this pattern before
				cursupcount = patterns[size-1][p]
				for i in p[0]: # for each src in p
					if i in atomic:
						for j in p[1]: # for each dest in p
							if j in atomic[i]:
								if nextts in atomic[i][j] and atomic[i][j][nextts]>=supatomicnumber:
									cursupcount+=1
				patterns[size][(p[0],p[1],expts)]=cursupcount
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
				patterns[size][(p[0],p[1],expts)]=cursupcount

		sortedpatterns = list(patterns[size].items())
		sortedpatterns.sort(key = lambda x: (x[1],x[0]), reverse=True)
		limit = K
		patterns[size].clear()
		for p in sortedpatterns[:limit]:
#			print(p)
			patterns[size][p[0]]=p[1]

		#patterns.append([])
		size += 1
		#if size == 10: break

	#for s in range(3,size):
	#	print('size:',s)
	#	print('number of patterns:',len(patterns[s]))
		#print(patterns[s])
	print('total number of patterns:',sum([len(patterns[s]) for s in range(3,size)]))

# yields next valid neighbor for an (extended) region
# other is another region that should not overlap with extension 
def next_neighbor(region, other):
	neighbors = set()
	for l in region:
		if l in neighbor:
			for n in neighbor[l]:
				if n not in neighbors and n not in other:
					neighbors.add(n)
	for n in neighbors:
		yield n
		
# gets valid neighbors for an (extended) region
# other is another region that should not overlap with extension 
def get_neighbors(region, other):
	neighbors = []
	for l in region:
		if l in neighbor:
			neighbors.extend(neighbor[l])
	neighbors = set(neighbors)
	neighbors.difference_update(region)
	neighbors.difference_update(other)
	return neighbors
	
# uses OD bitmap of atomic patterns and neighbor implementation
def improved8(K):
	triples = [{},{},{},{}] # records counted ODT triples
	patterns = [{},{},{},{}] # records counted ODT triples which are patterns (they satisfy minratio)
	dests = {} # records dests with non-zero atomic score for each src
	sources = {} # records sources with non-zero atomic score for each dest

	# st = time.time()
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
	print('number of atomic patterns:',len(patterns[3]))
	# et = time.time()
	# elapsed_time = et - st
	# print('Execution time of preprocessing of improved8:', elapsed_time, 'seconds')


	size = 4
#	numsavings = [0,0,0,0] # how many pprime we avoided counting
#	numfullcomp = [0,0,0,0] # how many pprime we fully counted
#	numgen = [0,0,0,0] # how many candidate ODT triples we generated
	while patterns[size-1] and size<=maxLevel:
		#print('level=',size)
		patterns.append({})
		triples.append({})
#		numsavings.append(0)
#		numfullcomp.append(0)
#		numgen.append(0)

		# try all minimal generalizations
		for p in patterns[size-1]:
			startingsupport = patterns[size-1][p]
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])
			# try to expand source
			nei = get_neighbors(p[0],p[1])
			for n in nei:
#			for n in next_neighbor(p[0],p[1]):
# 			for src in p[0]:
# 				if src in neighbor:
# 					for n in neighbor[src]:
#						numgen[size]+=1
						expsrc = tuple(sorted(list((p[0]+(n,)))))
						if (expsrc,p[1],p[2]) in triples[size]: continue # already examined this pattern before
						cursupcount = startingsupport
						if n in atomic and n not in p[0] and n not in p[1]:
							pprime = ((n,),p[1],p[2])
							#check if OD pair of pprime has at support at least one
							if n not in dests or not dests[n]&set(p[1]): # no chance to find any atomic pattern in pprime
#							if ((n,),p[1]) not in odpairs: # no chance to find any atomic pattern in pprime
#								numsavings[size] +=1
								pass
								# print('diff triple',pprime,'guaranteed to have 0 count')
							elif pprime in triples[1+len(p[1])+len(p[2])]: # pprime already counted
								cursupcount+= triples[1+len(p[1])+len(p[2])][pprime]
#								numsavings[size] +=1
							else:
#								numfullcomp[size]+=1
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
						patterns[size][(expsrc,p[1],p[2])]=cursupcount
						triples[size][(expsrc,p[1],p[2])]=cursupcount
						#odpairs.add((expsrc,p[1]))
			# try to expand dest
			nei = get_neighbors(p[1],p[0])
			for n in nei:
#			for n in next_neighbor(p[1],p[0]):
# 			for dest in p[1]:
# 				if dest in neighbor:
# 					for n in neighbor[dest]:
#						numgen[size]+=1
						expdest = tuple(sorted(list((p[1]+(n,)))))
						if (p[0],expdest,p[2]) in triples[size]: continue # already examined this pattern before
						cursupcount = startingsupport
						if n not in p[0] and n not in p[1]:
							pprime = (p[0],(n,),p[2])
							#check if OD pair of pprime has at support at least one
							if n not in sources or not sources[n]&set(p[0]): # no chance to find any atomic pattern in pprime
							#if (p[0],(n,)) not in odpairs: # no chance to find any atomic pattern in pprime
#								numsavings[size] +=1
								pass
								# print('diff triple',pprime,'guaranteed to have 0 count')
							elif pprime in triples[len(p[0])+1+len(p[2])]:
								cursupcount+= triples[len(p[0])+1+len(p[2])][pprime]
#								numsavings[size] +=1
							else:
#								numfullcomp[size]+=1
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
						patterns[size][(p[0],expdest,p[2])]=cursupcount
						triples[size][(p[0],expdest,p[2])]=cursupcount
						#odpairs.add((p[0],expdest))
			# try to expand timeslot (forward expansion)
			nextts = p[2][-1]+1
#			if nextts <= 47:
			if nextts <= 47 and nextts-p[2][0]<=timebound:
#				numgen[size]+=1
				expts = p[2]+(nextts,)
				if (p[0],p[1],expts) in triples[size]: continue # already examined this pattern before
				cursupcount = startingsupport
				pprime = (p[0],p[1],(nextts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
#					numsavings[size] +=1
				else:
#					numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if nextts in atomic[i][j] and atomic[i][j][nextts]>=supatomicnumber:
										cursupcount+=1
				patterns[size][(p[0],p[1],expts)]=cursupcount
				triples[size][(p[0],p[1],expts)]=cursupcount
			prevts = p[2][0]-1 # try backward expansion
			if prevts >= 0 and p[2][-1]-prevts<=timebound:
#				numgen[size]+=1
				expts = (prevts,)+p[2]
				if (p[0],p[1],expts) in triples[size]: continue # already examined this pattern before
				cursupcount = startingsupport
				pprime = (p[0],p[1],(prevts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
#					numsavings[size] +=1
				else:
#					numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if prevts in atomic[i][j] and atomic[i][j][prevts]>=supatomicnumber:
										cursupcount+=1
				patterns[size][(p[0],p[1],expts)]=cursupcount
				triples[size][(p[0],p[1],expts)]=cursupcount

		# sort patterns[size] based on supcount
		# delete patterns which are not top-ranked
		sortedpatterns = list(patterns[size].items())
		sortedpatterns.sort(key = lambda x: (x[1],x[0]), reverse=True)
		#print('level=',size,'\nsortedp:',sortedpatterns[:K])
		#print('size:',size,'range:',sortedpatterns[0][1],' -',sortedpatterns[min(K-1, len(sortedpatterns)-1)][1])
		# limit = K
		patterns[size].clear()
		for p in sortedpatterns[:K]:
			#print(p)
			patterns[size][p[0]]=p[1]
		size += 1

	#for s in range(3,size):
	#	print('size:',s)
		#print('number of patterns:',len(patterns[s]))
		#print(patterns[s])
#	print('number of saved pprime computations:',sum(numsavings), numsavings)
#	print('number of fully computed pprime:',sum(numfullcomp), numfullcomp)
	print('total number of patterns:',sum([len(patterns[s]) for s in range(3,size)]))
#	print('total number of generated ODT triples:',sum(numgen), numgen)


# simply uses heap to find top-k at each level
# uses top heap element to prune
# uses OD bitmap of atomic patterns and neighbor implementation
def prunerank(K):
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
	print('number of atomic patterns:',len(patterns[3]))

	size = 4
#	numsavings = [0,0,0,0] # how many pprime we avoided counting
#	numfullcomp = [0,0,0,0] # how many pprime we fully counted
#	numgen = [0,0,0,0] # how many candidate ODT triples we generated
	numheapsavings = [0,0,0,0] # how many pprime we avoided counting due to use of bounds and heap
	while patterns[size-1] and size<=maxLevel:
		#print('level=',size)
		patterns.append({})
		triples.append({})
#		numsavings.append(0)
#		numfullcomp.append(0)
#		numgen.append(0)
		numheapsavings.append(0)

		H = [] # heap with top-K patterns at this level

		# try all minimal generalizations
		for p in patterns[size-1]:
			startingsupport = patterns[size-1][p]
			#print(p)
			#print(patterns[size-1][p])
			# compute number of atomic triples in current pattern p
			#psize = len(p[0])*len(p[1])*len(p[2])
			# try to expand source
			nei = get_neighbors(p[0],p[1])
			for n in nei:
#			for n in next_neighbor(p[0],p[1]):
# 			for src in p[0]:
# 				if src in neighbor:
# 					for n in neighbor[src]:
#						numgen[size]+=1
						expsrc = tuple(sorted(list((p[0]+(n,)))))
						if (expsrc,p[1],p[2]) in triples[size]: continue # already examined this pattern before
						cursupcount = startingsupport
						if n in atomic and n not in p[0] and n not in p[1]:
							pprime = ((n,),p[1],p[2])
							#check if OD pair of pprime has at support at least one
							if n not in dests or not dests[n]&set(p[1]): # no chance to find any atomic pattern in pprime
#							if ((n,),p[1]) not in odpairs: # no chance to find any atomic pattern in pprime
#								numsavings[size] +=1
								pass
								# print('diff triple',pprime,'guaranteed to have 0 count')
							elif pprime in triples[1+len(p[1])+len(p[2])]: # pprime already counted
								cursupcount+= triples[1+len(p[1])+len(p[2])][pprime]
								# numsavings[size] +=1
							else:
								potential = len(p[1])*len(p[2]) # maximum potential support extension
								if len(H)==K and cursupcount+potential <= H[0][0]:
									# numheapsavings[size] +=1
									continue # pruned because it cannot enter top-k
								# numfullcomp[size]+=1
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
						#patterns[size][(expsrc,p[1],p[2])]=cursupcount
						triples[size][(expsrc,p[1],p[2])]=cursupcount
						if len(H)<K:
							heapq.heappush(H,(cursupcount,(expsrc,p[1],p[2])))
						#elif H[0][0]<cursupcount:
						elif H[0]<(cursupcount,(expsrc,p[1],p[2])):
							heapq.heapreplace(H,(cursupcount,(expsrc,p[1],p[2])))							#odpairs.add((expsrc,p[1]))
						#odpairs.add((expsrc,p[1]))
			# try to expand dest
			nei = get_neighbors(p[1],p[0])
			for n in nei:
#			for n in next_neighbor(p[1],p[0]):
# 			for dest in p[1]:
# 				if dest in neighbor:
# 					for n in neighbor[dest]:
						# numgen[size]+=1
						expdest = tuple(sorted(list((p[1]+(n,)))))
						if (p[0],expdest,p[2]) in triples[size]: continue # already examined this pattern before
						cursupcount = startingsupport
						if n not in p[0] and n not in p[1]:
							pprime = (p[0],(n,),p[2])
							#check if OD pair of pprime has at support at least one
							if n not in sources or not sources[n]&set(p[0]): # no chance to find any atomic pattern in pprime
							#if (p[0],(n,)) not in odpairs: # no chance to find any atomic pattern in pprime
								# numsavings[size] +=1
								pass
								# print('diff triple',pprime,'guaranteed to have 0 count')
							elif pprime in triples[len(p[0])+1+len(p[2])]:
								cursupcount+= triples[len(p[0])+1+len(p[2])][pprime]
								# numsavings[size] +=1
							else:
								potential = len(p[0])*len(p[2]) # maximum potential support extension
								if len(H)==K and cursupcount+potential <= H[0][0]:
									# numheapsavings[size] +=1
									continue # pruned because it cannot enter top-k
								# numfullcomp[size]+=1
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
						#patterns[size][(p[0],expdest,p[2])]=cursupcount
						triples[size][(p[0],expdest,p[2])]=cursupcount
						if len(H)<K:
							heapq.heappush(H,(cursupcount,(p[0],expdest,p[2])))
#							elif H[0][0]<cursupcount:
						elif H[0]<(cursupcount,(p[0],expdest,p[2])):
							heapq.heapreplace(H,(cursupcount,(p[0],expdest,p[2])))				
			#odpairs.add((p[0],expdest))
			# try to expand timeslot (forward expansion)
			nextts = p[2][-1]+1
#			if nextts <= 47:
			if nextts <= 47 and nextts-p[2][0]<=timebound:
				# numgen[size]+=1
				expts = p[2]+(nextts,)
				if (p[0],p[1],expts) in triples[size]: continue # already examined this pattern before
				cursupcount = startingsupport
				pprime = (p[0],p[1],(nextts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
					# numsavings[size] +=1
				else:
					potential = len(p[0])*len(p[1]) # maximum potential support extension
					if len(H)==K and cursupcount+potential <= H[0][0]:
						# numheapsavings[size] +=1
						continue # pruned because it cannot enter top-k
					# numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if nextts in atomic[i][j] and atomic[i][j][nextts]>=supatomicnumber:
										cursupcount+=1
				#patterns[size][(p[0],p[1],expts)]=cursupcount
				triples[size][(p[0],p[1],expts)]=cursupcount
				if len(H)<K:
					heapq.heappush(H,(cursupcount,(p[0],p[1],expts)))
				#elif H[0][0]<cursupcount:
				elif H[0]<(cursupcount,(p[0],p[1],expts)):
					heapq.heapreplace(H,(cursupcount,(p[0],p[1],expts)))
			prevts = p[2][0]-1 # try backward expansion
			if prevts >= 0 and p[2][-1]-prevts<=timebound:
				# numgen[size]+=1
				expts = (prevts,)+p[2]
				if (p[0],p[1],expts) in triples[size]: continue # already examined this pattern before
				cursupcount = startingsupport
				pprime = (p[0],p[1],(prevts,))
				if pprime in triples[len(p[0])+len(p[1])+1]:
					cursupcount+= triples[len(p[0])+len(p[1])+1][pprime]
					# numsavings[size] +=1
				else:
					potential = len(p[0])*len(p[1]) # maximum potential support extension
					if len(H)==K and cursupcount+potential <= H[0][0]:
						numheapsavings[size] +=1
						continue # pruned because it cannot enter top-k
					# numfullcomp[size]+=1
					for i in p[0]: # for each src in p
						if i in atomic:
							for j in p[1]: # for each dest in p
								if j in atomic[i]:
									if prevts in atomic[i][j] and atomic[i][j][prevts]>=supatomicnumber:
										cursupcount+=1
				#patterns[size][(p[0],p[1],expts)]=cursupcount
				triples[size][(p[0],p[1],expts)]=cursupcount
				if len(H)<K:
					heapq.heappush(H,(cursupcount,(p[0],p[1],expts)))
				#elif H[0][0]<cursupcount:
				elif H[0]<(cursupcount,(p[0],p[1],expts)):
					heapq.heapreplace(H,(cursupcount,(p[0],p[1],expts)))
	
		# sort patterns[size] based on supcount
		# delete patterns which are not top-ranked
		sortedpatterns = sorted(H, reverse=True)
		#sortedpatterns = sorted(H)

		patterns[size].clear()
		for p in sortedpatterns[:K]:
			patterns[size][p[1]]=p[0]

		if len(sortedpatterns)!=len(patterns[size]):
			print('!!!!!!!!',len(sortedpatterns), len(patterns[size]), len(H))

		size += 1

	#for s in range(3,size):
	#	print('size:',s)
		#print('number of patterns:',len(patterns[s]))
		#print(patterns[s])
#	print('number of saved pprime computations:',sum(numsavings), numsavings)
	print('number of saved pprime computations due to heap:',sum(numheapsavings), numheapsavings)
#	print('number of fully computed pprime:',sum(numfullcomp), numfullcomp)
	print('total number of patterns:',sum([len(patterns[s]) for s in range(3,size)]))
#	print('total number of generated ODT triples:',sum(numgen), numgen)





if len(sys.argv)!=8:
	print('Usage: python3 patterns <region_graph> <trips_graph> <support for atomic patterns> <support for extended patterns> <timebound> <k> <maxlevel>')
	exit()

# open trips file and compute atomic patterns

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
		else: # dest not seen before for this source
			atomic[l[0]][l[1]] = {l[2]:l[3]}
	else: # source not seen before
		atomic[l[0]] = {l[1]:{l[2]:l[3]}}

numatomic = len(flows)
supatomic = float(sys.argv[3])
minratio = float(sys.argv[4])
#rank = float(sys.argv[6])
K = int(sys.argv[6])
maxLevel = float(sys.argv[7])
supatomicnumber = sorted(flows, reverse=True)[int(supatomic*numatomic)]
print('number of atomic:',numatomic)
#print('supatomicnumber:',supatomicnumber)
timebound = int(sys.argv[5])-1

				
f = open(sys.argv[1])

neighbor = {}
for l in f:
	l = [int(x) for x in l.split()]
	if l[0]==l[1]: continue
	if l[0] in neighbor: # source already seen before
		neighbor[l[0]].append(l[1])
	else: # source not seen before
		neighbor[l[0]]=[l[1]]
	if l[1] in neighbor: # dest already seen before
		neighbor[l[1]].append(l[0])
	else: # dest not seen before
		neighbor[l[1]]=[l[0]]

st = time.time()
print('\nbaseline is running:\n')
baseline(K)	
et = time.time()
elapsed_time = et - st
print('Execution time of baseline:', elapsed_time, 'seconds')

# st = time.time()
# print('\nbaseline2 is running:\n')
# baseline_2(K)	
# et = time.time()
# elapsed_time = et - st
# print('Execution time of baseline2:', elapsed_time, 'seconds')

st = time.time()
print('\nimproved8 is running:\n')
improved8(K)
et = time.time()
elapsed_time = et - st
print('Execution time of improved8:', elapsed_time, 'seconds')

st = time.time()
print('\nprunerank is running:\n')
prunerank(K)
et = time.time()
elapsed_time = et - st
print('Execution time of prunerank:', elapsed_time, 'seconds')

