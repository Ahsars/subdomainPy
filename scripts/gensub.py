#CSM: Python Module for the Conventional Subdomain Modeling Approach
#   Copyright (C) 2017 
#   Computational Modeling Group, NCSU <http://www4.ncsu.edu/~jwb/>
#   Alper Altuntas <alperaltuntas@gmail.com>
#-------------------------------------------------------------------#
#   Modified by Xing Liu <xing.liu1990@outlook.com> on 12/18/2017
#       The script is modified to cross the land and island boundary 
#       of the Fulldomain, but it can not hold a case that include other
#       boundaries in the subdomain.
#-------------------------------------------------------------------#
import os
import sys
import numpy
from shutil import copyfile
from csm import Domain, SubShape

# gensub.py:
# Extracts a subdomain from a given full domain. Generates the following input
# files for the subdomain:
#   - fort.015  (required)
#   - fort.13   (optional)
#   - fort.14   (required)
#   - fort.26   (optional)

# Determines the nodes of a full domain that fall within a subdomain with 
# the given circular shape
def trimNodesCircle(full,sub,shape):

    sub.nodesTmp = [None]
    sub.subToFullNodeTmp = dict()
    sub.fullToSubNodeTmp = dict()
    sub.nodes = [None]
    sub.subToFullNode = dict()
    sub.fullToSubNode = dict()
    for n in range(1,len(full.nodes)):
        node = full.nodes[n]
        if ( (shape.x-node[0])**2 + (shape.y-node[1])**2 < (shape.r)**2):
            sub.subToFullNodeTmp[len(sub.nodesTmp)] = n
            sub.fullToSubNodeTmp[n] = len(sub.nodesTmp)
            sub.nodesTmp.append(node)
			
    # Get the number of the neighbor nodes and elements
    fullEles, fullNeighbors = neighborElementsAndNodes(full)
	
    # Initialize subdomain properties:
    sub.elements = [None]
    
    # Mapping from subdomain node numbering to full domain node numbering
    sub.subToFullEle = dict()

    # Loop through full domain elements and determine the ones inside the subdomain.
    # Also, determine the list of subdomain boundary nodes
    for e in range(1,len(full.elements)):
	
        ele = full.elements[e]
        # incSubNode[i] is True if i.th node of element e is in the subdomain
        incSubNode = [False]*3
        nSubNodes = 0
        for i in range(3):
            incSubNode[i] = ele[i] in sub.fullToSubNodeTmp    
            nSubNodes = nSubNodes + incSubNode[i]

        if nSubNodes==3:
											
            for i in range(3):
                if not ele[i] in sub.fullToSubNode:
                    node = full.nodes[ele[i]]
                    sub.fullToSubNode[ele[i]] = len(sub.nodes)
                    sub.subToFullNode[len(sub.nodes)] = ele[i]
                    sub.nodes.append(node)
					
            sub.subToFullEle[len(sub.elements)] = e
            sub.elements.append([sub.fullToSubNode[ele[0]], \
                                 sub.fullToSubNode[ele[1]], \
                                 sub.fullToSubNode[ele[2]]])
# Determines the nodes of a full domain that fall within a subdomain with 
# the given elliptical shape
def trimNodesEllipse(full,sub,shape):
    sub.nodes = [None]
    sub.subToFullNode = dict()
    sub.fullToSubNode = dict()
    for n in range(1,len(full.nodes)):
        node = full.nodes[n]
        #transform Global Coordinates to local coordinates
        X = node[0] - shape.c[0] 
        Y = node[1] - shape.c[1] 
        x = shape.cos*X - shape.sin*Y
        y = shape.sin*X + shape.cos*Y

        if(x**2/shape.xaxis**2 + y**2/shape.yaxis**2 < 1):
            sub.subToFullNode[len(sub.nodes)] = n
            sub.fullToSubNode[n] = len(sub.nodes)
            sub.nodes.append(node)

# Determines the elements of a full domain that fall within a subdomain
def trimElements(full,sub):

    # Get the number of the neighbor nodes and elements
    fullEles, fullNeighbors = neighborElementsAndNodes(full)
	
    # Initialize subdomain properties:
    #sub.elements = [None]
    sub.neta = 0            # total number of sub. boundary nodes
    sub.nbdvSet = set()        # set of sub. boundary nodes
    sub.isSubBoundary = [False]*(len(sub.nodes)+1) # True if i.th node is sub. boundary 
    
    # Mapping from subdomain node numbering to full domain node numbering
    #sub.subToFullEle = dict()

    # Loop through full domain elements and determine the ones inside the subdomain.
    # Also, determine the list of subdomain boundary nodes
    for e in range(1,len(full.elements)):
        ele = full.elements[e]
        boundaryNodeExist = False
        # incSubNode[i] is True if i.th node of element e is in the subdomain
        incSubNode = [False]*3
        nSubNodes = 0
        for i in range(3):
            incSubNode[i] = ele[i] in sub.fullToSubNode    
            nSubNodes = nSubNodes + incSubNode[i]

        if nSubNodes==3:
		
            # The element is inside the subdomain else if the number of 
            # the neighbor nodes is larger than the neighbor elements
            # in which it is considered as a boundary node:
            for i in range(3):
                if len(fullEles[ele[i]]) < len(fullNeighbors[ele[i]]):			
                    sub.nbdvSet.add(sub.fullToSubNode[ele[i]])
                    sub.isSubBoundary[sub.fullToSubNode[ele[i]]] = True
                    boundaryNodeExist = True	
									
#            sub.subToFullEle[len(sub.elements)] = e
#            sub.elements.append([sub.fullToSubNode[ele[0]], \
#                                 sub.fullToSubNode[ele[1]], \
#                                 sub.fullToSubNode[ele[2]]])


        elif not nSubNodes==0:
            # The element is outside the subdomain, but adjacent to subdomain.
            # Determine the boundary nodes:
            for i in range(3):
                if incSubNode[i]: # A boundary node should have at least 1 neighbor element including itself in the subdomain 
#                    neighborEleInSub = False    
#                    for neighborEle in fullEles[ele[i]]:  # check all neighbor elements of the node
#                        neighborEle = full.elements[neighborEle]
#                        isSubNode = [False]*3
#                        nNeighborSubNodes = 0
#                        for j in range(3):
#                            isSubNode[j] = neighborEle[j] in sub.fullToSubNode    
#                            nNeighborSubNodes = nNeighborSubNodes + isSubNode[j]                           	
#                        if nNeighborSubNodes==3:                  # all 3 nodes in the subdomain means an element is in subdomain
#                            neighborEleInSub = True 

#                    if neighborEleInSub == True:				
                    sub.nbdvSet.add(sub.fullToSubNode[ele[i]])
                    sub.isSubBoundary[sub.fullToSubNode[ele[i]]] = True
 #                   else:
 #                       node = full.nodes[ele[i]]
 #                       if node in sub.nodes:
 #                           print 'isolated node',node,'being deleted'
 #                           print 'nSubNodes=',len(sub.nodes)
 #                           sub.nodes.remove(node)
 #                           del sub.subToFullNode[sub.fullToSubNode[ele[i]]] 
 #   sub.subToFullNodeTmp = dict(zip(range(1,len(sub.subToFullNode)+1),sub.subToFullNode.values()))	
 #   del sub.subToFullNode
 #   del sub.fullToSubNode
 #   sub.subToFullNode = sub.subToFullNodeTmp
 #   sub.fullToSubNode = dict(zip(sub.subToFullNode.values(),sub.subToFullNode.keys()))
 #   del sub.subToFullNodeTmp
 #   return 	sub.subToFullNode

# Re-orders the list of boundary nodes of a subdomain
def neighborElementsAndNodes(full):

    # Determine the neighbors and elements of subdomain boundary nodes: 
    fullEles = [None]*(len(full.nodes)+1)        # set of elements for each node
    fullNeighbors = [None]*(len(full.nodes)+1)   # set of neighbors for each node	
    for i in range(1,len(full.nodes)+1):
        fullEles[i] = set()
        fullNeighbors[i] = set()
    for e in range(1,len(full.elements)):
        for i in range(3):
            node = full.elements[e][i]
            fullEles[node].add(e)
            if not full.elements[e][(i+1)%3] in fullNeighbors[node]:
                fullNeighbors[node].add(full.elements[e][(i+1)%3])
            if not full.elements[e][(i+2)%3] in fullNeighbors[node]:	
                fullNeighbors[node].add(full.elements[e][(i+2)%3])	
    return fullEles,fullNeighbors		

def orderBoundaryNodes(sub):

    # Determine the neighbors and elements of subdomain boundary nodes:
    eles = [None]*(len(sub.nodes)+1)        # set of elements for each node
    neighbors = [None]*(len(sub.nodes)+1)   # set of neighbors for each node
    for i in range(1,len(sub.nodes)+1):
        eles[i] = set()
        neighbors[i] = set()
    for e in range(1,len(sub.elements)):
        for i in range(3):
            node = sub.elements[e][i]
            if sub.isSubBoundary[node]:
                eles[node].add(e)
                neighbors[node].add(sub.elements[e][(i+1)%3])
                neighbors[node].add(sub.elements[e][(i+2)%3])

    # Initialize the list of ordered subdomain boundary nodes:
    sub.nbdv = []

    # True if a node is added to the reordered list of boundary nodes
    isAdded = [False]*(len(sub.nodes)+1)

    # Adds a given node to the ordered list of subdomain boundary nodes and 
    # removes it from the set of (unordered) subdomain boundary nodes 
    def addBoundaryNode(n):
        sub.nbdv.append(n)
        isAdded[n] = True
        sub.nbdvSet.remove(n)    

    # Re-order:
    addBoundaryNode(min(sub.nbdvSet))
    while (len(sub.nbdvSet)>0):
        progressed = False
        for neig in neighbors[sub.nbdv[-1]]:
            if (sub.isSubBoundary[neig] and not isAdded[neig]):
                nCommonEles = len(eles[sub.nbdv[-1]].intersection(eles[neig]))
                
                if nCommonEles==1:
                    addBoundaryNode(neig)
                    progressed = True
                    break
        if not progressed: 
            print("ERROR: Encountered error while reordering the list of boundary nodes.\n")
            exit()
            break

    # Set the number of boundary nodes:
    sub.neta = len(sub.nbdv) 


def writeFort14(sub,header):
    print("\t Writing fort.14 at",sub.dir)
    
    fort14 = open(sub.dir+"fort.14",'w')
   
    # Write header 
    fort14.write(header)
    fort14.write(str(len(sub.elements)-1) + " " + str(len(sub.nodes)-1)+"\n")
        
    # Write the list of nodes
    for n in range(1,len(sub.nodes)):
        node = sub.nodes[n]
        fort14.write("\t%d\t% 0.12f\t% 0.12f\t% 0.12f\n" \
                        %(n,node[0],node[1],node[2]))

    # Write the list of elements:
    for e in range(1,len(sub.elements)):
        ele = sub.elements[e]
        fort14.write(str(e) + "\t3\t" + str(ele[0]) +"\t"+ str(ele[1]) +"\t"+ str(ele[2]) +"\n")


    # Write the boundary list:
    orderBoundaryNodes(sub)        
    fort14.write("1\t!no. of subdomain boundary segments\n")
    fort14.write(str(sub.neta+1) + "\t!no. of subdomain boundary nodes\n")
    fort14.write(str(sub.neta+1) + "\n")
    for bn in sub.nbdv:
        fort14.write(str(bn)+"\n")
    fort14.write(str(sub.nbdv[0])+"\n")
    fort14.write("0\t!no. of land boundary segments\n0\t!no. of land boundary nodes")
    fort14.close()
       
def extractFort14(full,sub,shape):
    print("\nExtracting fort.14:")

    full.readFort14()

    # initialize nodal mapping containers
    sub.subToFullNode = None
    sub.fullToSubNode = None

    # Circular subdomain
    if (shape.typ=='c'):
        trimNodesCircle(full,sub,shape)
    # Elliptical subdomain:
    elif (shape.typ=='e'):
        trimNodesEllipse(full,sub,shape)
    else:
        print("ERROR: invalid subdomain shape type.")
        exit()

    trimElements(full,sub)
    writeFort14(sub,full.f14header)

def extractFort13(full,sub):
    print("Extracting fort.13:")

    print("\t Reading fort.13 at", full.dir)
    full13 = open(full.dir+"fort.13")
    print("\t Writing fort.13 at", sub.dir)
    sub13 = open(sub.dir+"fort.13","w")

    # Read-write header:
    sub13.write(full13.readline())

    # Number of nodes:
    full13.readline() # discard
    sub13.write(str(len(sub.nodes)-1)+"\n")

    # number of parameters:
    nParams = int(full13.readline().split()[0])
    sub13.write(str(nParams)+"\n")

    # Default parameter values:
    for p in range(nParams):
        for i in range(4):
            sub13.write(full13.readline())

   
    # Write non-default parameter values: 
    for p in range(nParams):
            
        sub13.write(full13.readline()) # parameter name
        nFullNodes = int(full13.readline().split()[0])

        lines = []      
        snode = 1
        def full(snode): return sub.subToFullNode[snode]
#        fnode_last = full(len(sub.nodes)-1)
        fnode_last = max(sub.subToFullNode)

        for f in range(nFullNodes):

            sline = full13.readline().split()                   
            fnode = int(sline[0])
            if fnode in sub.fullToSubNode:
                snode = sub.fullToSubNode[fnode]	
                lines.append([snode,sline])  	
        	
#        		  
#            if (not fnode>fnode_last):
#
#                while fnode > full(snode) and snode < len(sub.nodes)-1:
#                    snode += 1
#    
#                if fnode == full(snode):
#                    lines.append([snode,sline]) 


        sub13.write(str(len(lines))+"\n")
        for l in lines:
            sub13.write(str(l[0])+"\t")
            for i in range(1,len(l[1])):
                sub13.write(l[1][i]+"\t")
            sub13.write("\n")

    sub13.close() 
    full13.close() 
    
# Write subdomain control file of the subdomain
def writeFort015(sub):
    print("Generating fort.015 at", sub.dir)
    fort015 =  open(sub.dir+"fort.015", 'w')
    fort015.write( "0" + "\t!NOUTGS" + '\n' )
    fort015.write( "0" + "\t!NSPOOLGS" + '\n' )
    fort015.write( "1" + "\t!enforceBN" + '\n' )    # type-1 b.c. by default
    fort015.write( "0" + "\t!ncbnr" + '\n' )    
    fort015.close() 

# Writes nodal and elemental mapping files of the subdomain:
def writeNewToOld(sub):
    print("Generating nodal and elemental mapping files at", sub.dir)

    py140 = open(sub.dir+"py.140","w")
    py140.write("Nodal mapping from sub to full\n")
    for i in range(1,len(sub.subToFullNode)+1):
        py140.write(str(i)+" "+str(sub.subToFullNode[i])+"\n")
    py140.close()
        
    py141 = open(sub.dir+"py.141","w")
    py141.write("Elemental mapping from sub to full\n")
    for i in range(1,len(sub.subToFullEle)+1):
        py141.write(str(i)+" "+str(sub.subToFullEle[i])+"\n")
    py141.close()
    
    

def copySwanFiles(full,sub):
    print("Copying SWAN input files to", sub.dir)
    copyfile(full.dir+"fort.26",sub.dir+"fort.26")    
    copyfile(full.dir+"swaninit",sub.dir+"swaninit")    

# Generate the input files of the subdomain
def main(fullDir,subDir):

    print("")
    print('\033[95m'+'\033[1m'+"NCSU Subdomain Modeling for ADCIRC+SWAN"+'\033[0m')
    print("")

    print("Generating input files for the subdomain at", subDir)

    # Initialize the full and subdomains
    full = Domain(fullDir)
    sub = Domain(subDir)

    # Read subdomain shape file:
    shape = SubShape(sub.dir)
         
    # Extract fort.14:
    if not os.path.exists(full.dir+"fort.14"):
        print("ERROR: No fort.14 file exists at", full.dir)
        exit()
    else:
        extractFort14(full,sub,shape)  
 
    # Extract fort.13:
    if os.path.exists(full.dir+"fort.13"):
        extractFort13(full,sub)

    # Generate fort.015:
    writeFort015(sub)
    
    # Generate py.140 and py.141
    writeNewToOld(sub)

    # Copy SWAN input files
    if full.isCoupledAdcircSwan():
        copySwanFiles(full,sub)

    # The final log message:
    print("\nSubdomain input files are now ready.")
    print('\033[91m'+"\nImportant Note:"+'\033[0m')
    print("fort.15 and meteorological files have to be generated manually ")
    print("by the user as described in Subdomain Modeling User Guide.\n")

def usage():
    scriptName = os.path.basename(__file__)
    print("")
    print("Usage:")
    print(" ", scriptName, "fulldomainDir subdomainDir\n")


if __name__== "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1],sys.argv[2])
    else:
        usage()
