/*
===============================================================================
                                                                        R1INP.C
                                                               Parameters input
===============================================================================
*/
#include <stdio.h>
 
#define SKIP  fgets(dummy,100,fin)
#define SKIP1 while(1){fscanf(fin,"%c",&ch);if(ch=='=')break;}

extern int   range,ctiv,repr,ai,ier1;
extern char  mmode[];
extern FILE *fopen(),*fin,*fflog;
 
void r1inp (float *ro,float *th,long *maxm,int *npr,float *rpi,float *eta,
            int *us)
{
float fr;
char  ccti[100],crang[100],crep[100],dummy[110],ch;
 
      fin=fopen("rpar.gr","r");
      if (fin==NULL)
        { fprintf(fflog,"\n*** ERROR IN OPENING rpar.gr\n\n"); ier1=1; return;}

      SKIP1;fscanf(fin,"%s",mmode);  SKIP;       /* match mode(dock/hel/ovlp)*/
      SKIP1;fscanf(fin,"%f",eta);    SKIP;       /* grid step                */

         ro[0]=0.;                               /* background               */
         ro[1]=1.;                               /* B                        */
      SKIP1;fscanf(fin,"%f",&ro[2]); SKIP;       /* A, core                  */
         ro[2]=-ro[2];
         ro[3]=ro[2];                            /* A, in                    */
         ro[4]=1.;                               /* A, on                    */
      SKIP1;fscanf(fin,"%f",&fr);    SKIP;
         ro[5]=fr*ro[4];                         /* A, out                   */

      SKIP1;fscanf(fin,"%s",crang);  SKIP;       /* pot.range(gr.st / at.rad)*/
         if((crang[0]=='a')||(crang[0]=='A')) range=0; else {
         if((crang[0]=='g')||(crang[0]=='G')) range=1; else {
         fprintf(fflog,"\n*** ERROR: illegal parameter %s\n\n",crang);
         ier1=1; return;                                   }}

      SKIP1;fscanf(fin,"%s",ccti);   SKIP;       /* projection cumul. or not */
         if((ccti[0]=='b')||(ccti[0]=='B')) ctiv=0; else {
         if((ccti[0]=='g')||(ccti[0]=='G')) ctiv=1; else {
         fprintf(fflog,"\n*** ERROR: illegal parameter %s\n\n",ccti);
         ier1=1; return;                                   }}

      SKIP1;fscanf(fin,"%s",crep);   SKIP;       /* all/hydrophobic/c-alpha  */
         if((crep[0]=='a')||(crep[0]=='A')) repr=0; else {
         if((crep[0]=='h')||(crep[0]=='H')) repr=1; else {
         if((crep[0]=='c')||(crep[0]=='C')) repr=2; else {
         fprintf(fflog,"\n*** ERROR: illegal parameter %s\n\n",crep);
         ier1=1; return;                                   }}}

         *th=0.;                                 /* threshold(rel.) for peaks*/

      SKIP1;fscanf(fin,"%ld",maxm);  SKIP;       /* no.of matches out        */
         *npr=20;                                /* no.of peaks per orient.  */
         *rpi=0.;                                /* radius of peak identity  */
      SKIP1;fscanf(fin,"%d",&ai);    SKIP;       /* angle interval for rotat.*/

      fclose(fin);
}
