/*
===============================================================================
                                                                        R1GLO.H
                                                               Global variables
===============================================================================
g,g1                     - grid arrays
x,y,z,x_1,y_1,z_1        - atom coordinates
ra                       - radius of atom
hy                       - hydrophobicity of atom
typat                    - type of atom
atmnam,atmnbr            - atom name and number
resnam,rnber,resn        - residue name, number, numerical ID
inn                      - index for atoms sorting
orn                      - Euler angles
mmode                    - matching mode
antip                    - parallel/antiparallel id for helices
range                    - potential range (grid step or atom radius)
ctiv                     - projection cumulative or not
repr                     - all/hydrophobic/c-alpha
ai                       - angle interval for rotation
maxa                     - maximum angle between helices
h1uvw                    - main axis vector (transformed coordinates)
xa1,ya1,...,za2          - first & last atoms for helix 1 (original coord)
pk                       - peaks
sh                       - shifts (in pixels)
ws                       - work  (for sorting)
ind                      - index (for sorting)
in                       - index (for peaks)
ino                      - index (of orientations)
npx                      - no. of pixels at each dimension
NG2,NG2_2,NG2_3,ng3      - 2*npx,2*npx*npx,2*npx*npx*npx,npx*npx*npx
w1,w2,w3                 - work
xb0,yb0,zb0              - mol.B center of mass in initial coordinates
nuro,nuron,nurtog        - residues of the binding site (overlap)
gic,ggic,wgic            - global counters (thru all molecules)
nuhit,hita,hitb,hsto     - number of hits (for evaluation)
avdis,rda,rdb            - average R-L distance and radii (for evaluation)
gmatch                   - global match counter (for evaluation)
ier1,2                   - error codes
------------------------------------------------------------------------------
Parallel variables:
myProc		        - unique process identifier
nProc				  - total number of executing processes
-----------------------------------------------------------------------------*/
float g[DIMG],g1[DIMG];
float x[DIM1],y[DIM1],z[DIM1],x_1[DIM1],y_1[DIM1],z_1[DIM1];
float x_orig[DIM1],y_orig[DIM1],z_orig[DIM1];
float ra[DIM1][2],hy[DIM1][2];
float ws[DIMS],h1uvw[5];
float ng3;
float xb0,yb0,zb0,xa1,ya1,za1,xa2,ya2,za2;
float avdis,rda,rdb;
long  sh[DIMP],in[DIMP],ino[DIMP],ind[DIMS];
long  w1[DIM4+2],w2[DIM4+2],w3[DIM4+2];
long  NG2,NG2_2,NG2_3,ggic,gmatch;
int   orn[DIM3][3];
int   pk[DIMP];
int   inn[DIM1][2],atmnbr[DIM1][2],resn[DIM1][2],rnber[DIM1][2];
int   nuro[DIM11],nuhit[11],hita[1000][200],hitb[1000][200];
int   hsto1[1002],hsto2[1002],hsto3[1002],hsto4[1002],hsto5[1002];
int   npx,range,ctiv,repr,ai,maxa,nuron,nurtog,gic,wgic,ier1,ier2;
char  typat[DIM1][2][4],atmnam[DIM1][2][4],resnam[DIM1][2][4];
char  mmode[20],antip[20];
FILE  *fopen(),*fin,*finn,*fic,*foc,*fok,*fop,*fol,*fres,*fcon,*fflog;

/* Parallel variables */
int   		myProc, nProc;
MPI_Comm	c_comm, r_comm;
MPI_Group 	MPI_GROUP_WORLD;
MPI_Status 	*mpi_status;
