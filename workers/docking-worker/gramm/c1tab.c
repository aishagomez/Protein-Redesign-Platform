/*
==========================================================================================================
                                                                                                   C1TAB.C
                                                            Table of REC atom types for PDB atoms-residues
==========================================================================================================
*/
#include <string.h>

void c1tab(t)

char  t[][50*4];
{

/*                     ------------------------------------------------------------------------------------*/
/*                     ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL XXX */
/*                     ------------------------------------------------------------------------------------*/
/* N   */strcpy(t[ 1],"N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 N14 ");
/* ND1 */strcpy(t[ 2],"                                N13                                             N13 ");
/* ND2 */strcpy(t[ 3],"        N14                                                                     N14 ");
/* NE  */strcpy(t[ 4],"    N13                                                                         N13 ");
/* NE1 */strcpy(t[ 5],"                                                                    N13         N13 ");
/* NE2 */strcpy(t[ 6],"                    N14         N13                                             N13 ");
/* NH1 */strcpy(t[ 7],"    N13                                                                         N13 ");
/* NH2 */strcpy(t[ 8],"    N13                                                                         N13 ");
/* NZ  */strcpy(t[ 9],"                                            N13                                 N13 ");
/* C   */strcpy(t[10],"C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  C7  ");
/* CA  */strcpy(t[11],"C6  C6  C6  C6  C6  C6  C6  C6  C6  C6  C6  C6  C6  C6  CH  C6  C6  C6  C6  C6  C6  ");
/* CB  */strcpy(t[12],"CH3 CH2 CH2 CH2 CH2 CH2 CH2     CH2 CH  CH2 CH2 CH2 CH2 CH2 CH2 CH  CH2 CH2 CH  CH2 ");
/* CD  */strcpy(t[13],"    CH2             C7  C7                  CH2         CH2                     CH2 ");
/* CD1 */strcpy(t[14],"                                    CH3 CH3         CHR             CHR CHR     CH3 ");
/* CD2 */strcpy(t[15],"                                C8      CH3         CHR             C8  CHR     CH3 ");
/* CE  */strcpy(t[16],"                                            CH2 CH3                             CH3 ");
/* CE1 */strcpy(t[17],"                                C8                  CHR                 CHR     CHR ");
/* CE2 */strcpy(t[18],"                                                    CHR             C8  CHR     CHR ");
/* CE3 */strcpy(t[19],"                                                                    CHR         CHR ");
/* CG  */strcpy(t[20],"    CH2 C7  C7      CH2 CH2     C8      CH  CH2 CH2 C8  CH2         C8  C8      C8  ");
/* CG1 */strcpy(t[21],"                                    CH3                                     CH3 CH3 ");
/* CG2 */strcpy(t[22],"                                    CH2                         CH3         CH3 CH3 ");
/* CH2 */strcpy(t[23],"                                                                    CHR         CHR ");
/* CZ  */strcpy(t[24],"    C6                                              CHR                 C8      C8  ");
/* CZ2 */strcpy(t[25],"                                                                    CHR         CHR ");
/* CZ3 */strcpy(t[26],"                                                                    CHR         CHR ");
/* O   */strcpy(t[27],"O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 O17 ");
/* OD1 */strcpy(t[28],"        O17 O17-                                                                O17 ");
/* OD2 */strcpy(t[29],"            O17-                                                                O17 ");
/* OE1 */strcpy(t[30],"                    O17 O17-                                                    O17 ");
/* OE2 */strcpy(t[31],"                        O17-                                                    O17 ");
/* OG  */strcpy(t[32],"                                                            O18                 O17 ");
/* OG1 */strcpy(t[33],"                                                                O18             O17 ");
/* OH  */strcpy(t[34],"                                                                        O18     O17 ");
/* OXT */strcpy(t[35],"O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-O17-");
/* SD  */strcpy(t[36],"                                                S20                             S20 ");
/* SG  */strcpy(t[37],"                S20                                                             S20 ");
/* X   */strcpy(t[38],"X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   X   ");
}
