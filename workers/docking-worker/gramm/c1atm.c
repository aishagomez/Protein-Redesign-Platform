/*
===============================================================================
                                                                        C1ATM.C
                                                 Atom types from PDB as numbers
===============================================================================
*/
#include <string.h>

int c1atm(char *atyp)
{

      if (strcmp(atyp," N  ")==0) return  (1);
      if (strcmp(atyp," ND1")==0) return  (2);
      if (strcmp(atyp," ND2")==0) return  (3);
      if (strcmp(atyp," NE ")==0) return  (4);
      if (strcmp(atyp," NE1")==0) return  (5);
      if (strcmp(atyp," NE2")==0) return  (6);
      if (strcmp(atyp," NH1")==0) return  (7);
      if (strcmp(atyp," NH2")==0) return  (8);
      if (strcmp(atyp," NZ ")==0) return  (9);
      if (strcmp(atyp," C  ")==0) return (10);
      if (strcmp(atyp," CA ")==0) return (11);
      if (strcmp(atyp," CB ")==0) return (12);
      if (strcmp(atyp," CD ")==0) return (13);
      if (strcmp(atyp," CD1")==0) return (14);
      if (strcmp(atyp," CD2")==0) return (15);
      if (strcmp(atyp," CE ")==0) return (16);
      if (strcmp(atyp," CE1")==0) return (17);
      if (strcmp(atyp," CE2")==0) return (18);
      if (strcmp(atyp," CE3")==0) return (19);
      if (strcmp(atyp," CG ")==0) return (20);
      if (strcmp(atyp," CG1")==0) return (21);
      if (strcmp(atyp," CG2")==0) return (22);
      if (strcmp(atyp," CH2")==0) return (23);
      if (strcmp(atyp," CZ ")==0) return (24);
      if (strcmp(atyp," CZ2")==0) return (25);
      if (strcmp(atyp," CZ3")==0) return (26);
      if (strcmp(atyp," O  ")==0) return (27);
      if (strcmp(atyp," OD1")==0) return (28);
      if (strcmp(atyp," OD2")==0) return (29);
      if (strcmp(atyp," OE1")==0) return (30);
      if (strcmp(atyp," OE2")==0) return (31);
      if (strcmp(atyp," OG ")==0) return (32);
      if (strcmp(atyp," OG1")==0) return (33);
      if (strcmp(atyp," OH ")==0) return (34);
      if (strcmp(atyp," OXT")==0) return (35);
      if (strcmp(atyp," SD ")==0) return (36);
      if (strcmp(atyp," SG ")==0) return (37);

      

      if ((atyp[0]=='H')||(atyp[1]=='H')) return(0);      /* H   */

                                  return (38);        /* Unknown */
}
