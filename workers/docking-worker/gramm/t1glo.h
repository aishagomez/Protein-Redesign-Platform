/*
===============================================================================
                                                                        T1GLO.H
                                                               Global variables
===============================================================================
xtp,ytp,ztp                   - templates CA coordinates
xca,yca,zca                   - mol A & B CA coordinates 
rmsda/b                       - rmsd target on template
tmsa/b                        - TM-score target on template
tra/b                         - translation target to template
ura/b                         - rotation target to template
nrt                           - total number of template residues
trnum                         - residue individual number in templates
rrnber                        - residue individual number in mol A & B
seqa/b                        - seq ID target on template
cova/b                        - alignment coverage target on template
tna/b                         - names of valid templates for the target
ltna/b,ltra/b,lura/b          - temp arrays for parallel transfer
tnam                          - names of all templates
trnam                         - names of residues in templates
rresnam                       - names of residues in mol A & B
amode                         - alignment mode
-----------------------------------------------------------------------------*/
float xtp[DIMT][DIM11][2],ytp[DIMT][DIM11][2],ztp[DIMT][DIM11][2];
float xca[DIM11][2],yca[DIM11][2],zca[DIM11][2];
float rmsda[DIMT*2],rmsdb[DIMT*2],tmsa[DIMT*2],tmsb[DIMT*2];
float tra[DIMT*2][4],trb[DIMT*2][4],ura[DIMT*2][10],urb[DIMT*2][10];
float ltra[DIMT*2*3],ltrb[DIMT*2*3],lura[DIMT*2*9],lurb[DIMT*2*9];
float xk[DIM1+1],yk[DIM1+1],zk[DIM1+1];
float wf1[DIMT*2],wf2[DIMT*2],wf3[DIMT*2],wf4[DIMT*2];
int   nrt[DIMT][2],trnum[DIMT][DIM11][2],rrnber[DIM11][2];
int   seqa[DIMT*2],seqb[DIMT*2],cova[DIMT*2],covb[DIMT*2];
int   wi1[DIMT*2],wi2[DIMT*2],wi3[DIMT*2],wi4[DIMT*2];
char  tnam[DIMT*2][20],tna[DIMT*2][20],tnb[DIMT*2][20];
char  ltna[DIMT*2*20],ltnb[DIMT*2*20];
char  trnam[DIMT][DIM11][2][3],rresnam[DIM11][2][3];
char  wc1[DIMT*2][20],wc2[DIMT*2][20];
char  amode[20];
