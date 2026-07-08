/*
===============================================================================
                                                                        R1PRR.C
                                                         Read orientation array
===============================================================================
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
 
extern int   orn[][3];
extern int   ai,ier1;
extern FILE  *fopen(),*fin,*fflog;
 
void r1prr (long *nor)
{
long  ir;
int   i,ii,dlen;
char  dummy[82],dadr[200],*dadi;
 
      if (ai==0)
        {
         *nor=1;                                          /* No.of rotations */
         orn[1][0]=0; orn[1][1]=0; orn[1][2]=0;
        }
      else
        {
         dadi=getenv("GRAMMDAT"); 
         if (dadi==NULL)
           { fprintf(fflog,"\n*** ERROR: environment variable GRAMMDAT");
             fprintf(fflog," is not defined\n\n"); ier1=1; return;       }

         dlen=strlen(dadi); ii=-1;
         for (i=0; i<dlen; i++) { dadr[++ii]=dadi[i]; }
         dadr[++ii]='/'; dadr[++ii]='a'; dadr[++ii]='n'; dadr[++ii]='g';

         if (ai== 5) { dadr[++ii]='0'; dadr[++ii]='5'; }  else { 
         if (ai== 6) { dadr[++ii]='0'; dadr[++ii]='6'; }  else {
         if (ai== 7) { dadr[++ii]='0'; dadr[++ii]='7'; }  else {
         if (ai== 8) { dadr[++ii]='0'; dadr[++ii]='8'; }  else {
         if (ai== 9) { dadr[++ii]='0'; dadr[++ii]='9'; }  else {
         if (ai==10) { dadr[++ii]='1'; dadr[++ii]='0'; }  else { 
         if (ai==12) { dadr[++ii]='1'; dadr[++ii]='2'; }  else {
         if (ai==15) { dadr[++ii]='1'; dadr[++ii]='5'; }  else {
         if (ai==18) { dadr[++ii]='1'; dadr[++ii]='8'; }  else {
         if (ai==20) { dadr[++ii]='2'; dadr[++ii]='0'; }  else {
         if (ai==30) { dadr[++ii]='3'; dadr[++ii]='0'; }  else {
         if (ai==40) { dadr[++ii]='4'; dadr[++ii]='0'; }  else {
         if (ai==50) { dadr[++ii]='5'; dadr[++ii]='0'; }  else {
         if (ai==60) { dadr[++ii]='6'; dadr[++ii]='0'; }  else {
         if (ai==70) { dadr[++ii]='7'; dadr[++ii]='0'; }  else {
         if (ai==80) { dadr[++ii]='8'; dadr[++ii]='0'; }  else {
         if (ai==90) { dadr[++ii]='9'; dadr[++ii]='0'; }  else {

         fprintf(fflog,"\n*** ERROR: %d deg angle set is not installed\n\n",
                 ai); ier1=1; return;          }}}}}}}}}}}}}}}}}

         dadr[++ii]='.'; dadr[++ii]='d'; dadr[++ii]='a'; dadr[++ii]='t';  
         dadr[++ii]='\0'; 

         fin=fopen(dadr,"r");   
       
         if (fin==NULL)
           { fprintf(fflog,"\n*** ERROR IN OPENING ang%d.dat\n\n",ai);
             ier1=1;return; }

         fscanf(fin,"%ld",nor); fgets(dummy,81,fin);
         for (ir=1l; ir<=*nor; ir+=1l)
           {
            fscanf(fin,"%d%d%d",&orn[ir][0],&orn[ir][1],&orn[ir][2]);
           }
         fclose(fin);
        }
}
