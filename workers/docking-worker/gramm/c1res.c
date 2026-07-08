/*
===============================================================================
                                                                        C1RES.C
                                                         Residue name to number
===============================================================================
*/
#include <string.h>

int c1res(char *ares)
{
      while (1)
        {
         if (strcmp(ares," ALA")==0) return  (1);
         if (strcmp(ares," ARG")==0) return  (2);
         if (strcmp(ares," ASN")==0) return  (3);
         if (strcmp(ares," ASP")==0) return  (4);
         if (strcmp(ares," CYS")==0) return  (5);
         if (strcmp(ares," GLN")==0) return  (6);
         if (strcmp(ares," GLU")==0) return  (7);
         if (strcmp(ares," GLY")==0) return  (8);
         if (strcmp(ares," HIS")==0) return  (9);
         if (strcmp(ares," ILE")==0) return (10);
         if (strcmp(ares," LEU")==0) return (11);
         if (strcmp(ares," LYS")==0) return (12);
         if (strcmp(ares," MET")==0) return (13);
         if (strcmp(ares," PHE")==0) return (14);
         if (strcmp(ares," PRO")==0) return (15);
         if (strcmp(ares," SER")==0) return (16);
         if (strcmp(ares," THR")==0) return (17);
         if (strcmp(ares," TRP")==0) return (18);
         if (strcmp(ares," TYR")==0) return (19);
         if (strcmp(ares," VAL")==0) return (20);


         if (ares[0]=='1') { ares[0]=' '; continue; }
         if (ares[0]=='2')           return  (0);
         if (ares[0]=='A') { ares[0]=' '; continue; }
         if (ares[0]=='B')           return  (0);

                                     return (21);   /* Unknown */
        }
}
