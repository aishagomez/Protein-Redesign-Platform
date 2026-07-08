/*
===============================================================================
                                                                        R1US6.C
                                                                  User's module
                                     Criterion 1, helix, interface-noninterface
===============================================================================
*/
#include <stdio.h>
#include <math.h>

extern float xb0,yb0,zb0,xa1,ya1,za1,xa2,ya2,za2;
extern long  ggic;
extern int   nuhit[],gic,ier1;
extern FILE  *fopen(),*fic,*foc,*fflog;

static float k,l,m,k1,l1,m1,k2,l2,m2,c1,c2;
static int   sec,hsec,nh;

void r1us6 (int irr,float xt,float yt,float zt)
{
float xh_1,yh_1,zh_1,xh_2,yh_2,zh_2,xc_1,yc_1,zc_1,xc_2,yc_2,zc_2;
float x,y,z,f,xc,yc,zc,kc,lc,mc,cc,ch1,ch2,f1,f2,chh;
int   ang1,ang2,angh,iper,i;
char  dummy[110];

/*--------------------------------------------------------------- First time */
      if (gic==0)
        {                                                      /* Open files */
         foc=fopen("1.cri","w");
/*       fprintf(foc,"\n"); */

         fic=fopen("rcr1.gr","r");
         if (fic==NULL) 
           { fprintf(fflog,"\n*** ERROR in opening rcr1.gr\n\n"); ier1=1;
             return; }

                                       /* Read sector of the interface [deg] */
         fgets(dummy,100,fic); fgets(dummy,100,fic); fgets(dummy,100,fic);
         fscanf(fic,"%d",&sec); hsec=sec/2;
         fgets(dummy,100,fic); fgets(dummy,100,fic); fgets(dummy,100,fic);

                                /* Read no.of hits to analyze per helix pair */
         fscanf(fic,"%d",&nh);
         fgets(dummy,100,fic); fgets(dummy,100,fic); fgets(dummy,100,fic);
         fgets(dummy,100,fic); fgets(dummy,100,fic); fgets(dummy,100,fic);

         gic++;                                     /* Change global counter */
        }
/*------------------------------------------------- Process individual pairs */

      if (irr==1)
        {         /* Read alternative coordinates of correct ligand position */
         fscanf(fic,"%s%f%f%f",dummy,&xh_2,&yh_2,&zh_2); fgets(dummy,100,fic);

         for (i=0; i<10; i++) nuhit[i]=0;   /* No.of hits in diff. mol.areas */

         xh_1=xb0; yh_1=yb0; zh_1=zb0;     /* 'real' correct ligand position */

         k=xa2-xa1; l=ya2-ya1; m=za2-za1;

         f1 = k*xh_1 + l*yh_1 + m*zh_1 + ((l*l+m*m)/k)*xa1 - l*ya1 - m*za1;
         f2 = k*xh_2 + l*yh_2 + m*zh_2 + ((l*l+m*m)/k)*xa1 - l*ya1 - m*za1;

         xc_1=f1/(k+(l*l+m*m)/k);   /* Centr.point of the 1st correct vector */
         yc_1=(l/k)*(xc_1-xa1)+ya1;
         zc_1=(m/k)*(xc_1-xa1)+za1;

         k1=xh_1-xc_1; l1=yh_1-yc_1; m1=zh_1-zc_1; 
         c1=(float)sqrt((double)(k1*k1+l1*l1+m1*m1));

         xc_2=f2/(k+(l*l+m*m)/k);   /* Centr.point of the 2nd correct vector */
         yc_2=(l/k)*(xc_2-xa1)+ya1;
         zc_2=(m/k)*(xc_2-xa1)+za1;

         k2=xh_2-xc_2; l2=yh_2-yc_2; m2=zh_2-zc_2;
         c2=(float)sqrt((double)(k2*k2+l2*l2+m2*m2));

         chh=(k2*k1+l2*l1+m2*m1)/(c2*c1);
         chh=(float)acos((double)chh); angh=(int)(chh*57.3);
/*printf("\nANGH=%d",angh);*/
        }

      if (irr>nh) return;                 /* Check max no.of hits to analyze */

      x=xb0+xt; y=yb0+yt; z=zb0+zt;               /* Current hit coordinates */

      f = k*x + l*y + m*z + ((l*l+m*m)/k)*xa1 - l*ya1 - m*za1;

      xc=f/(k+(l*l+m*m)/k);         /* Centr.point of the current hit vector */
      yc=(l/k)*(xc-xa1)+ya1;
      zc=(m/k)*(xc-xa1)+za1;
      kc=x-xc; lc=y-yc; mc=z-zc;
      cc=(float)sqrt((double)(kc*kc+lc*lc+mc*mc));

                                     /* Angles curr.-corr.1 and curr.-corr.2 */
      ch1=(kc*k1+lc*l1+mc*m1)/(cc*c1);
      ch1=(float)acos((double)ch1); ang1=(int)(ch1*57.3);
      ch2=(kc*k2+lc*l2+mc*m2)/(cc*c2);
      ch2=(float)acos((double)ch2); ang2=(int)(ch2*57.3);

      if ((ang1<=hsec)||(ang2<=hsec)) nuhit[0]++;     /* Check the hit angle */

      if (irr==nh) 
        {
         iper=(int)((((float)nuhit[0])/((float)nh))*100.);
/*       fprintf(foc," %3d",iper); */
         ggic+=iper;
/*printf("nuhit=%2d  ggic=%4ld\n",nuhit[0],ggic);*/
        }
}
