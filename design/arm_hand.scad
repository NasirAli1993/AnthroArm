/*
ANTHRO / 25 — adult-scale dexterous tabletop arm
Parametric review CAD. Local units mm. See robot_spec.json for canonical joints.
5 arm axes + 20 independently controlled hand axes, including thumb opposition.
Select each FreeCAD component for an embedded explanation in the native model.
Hardware concept only: motors, bearings, tendon routing and tolerances unvalidated.
*/
include <robot_parameters.scad>

/* [View] */
pose = "home"; // [home,zero,grasp]
show_labels = true;
show_pads = true;
show_hardware = true;
view_hand_only = false;
// Set a canonical link name to inspect an isolated link in its own local frame.
export_part = "";

/* [Design] */
hinge_pin_diameter = 2.1;
tendon_bore_diameter = 1.4;
palm_width = 84;
palm_length = 100;
palm_thickness = 32;
shell_wall = 4;

/* [Preview quality] */
$fn = 36;
white = [.91,.94,.96];
blue = [.11,.24,.34];
dark = [.08,.105,.13];
orange = [.98,.50,.16];
rubber = [.12,.15,.17];

// Rounded boxes preserve exact external dimensions.
module roundbox(size, r=2) {
    translate([r,r,r]) hull()
        for (x=[0,size[0]-2*r], y=[0,size[1]-2*r], z=[0,size[2]-2*r])
            translate([x,y,z]) sphere(r=r);
}
module ycylinder(r,h) { rotate([-90,0,0]) cylinder(r=r,h=h); }
module xcy(r,h) { rotate([0,90,0]) cylinder(r=r,h=h); }
module capsulebar(l,r,w) {
    hull() for(z=[0,l]) translate([0,-w/2,z]) ycylinder(r,w);
}

// Rigid bench fixture. M8 mounting holes and rear cable slot.
module base() {
    color(dark) difference() {
        cylinder(r=120,h=80);
        translate([0,0,-1]) cylinder(r=14,h=82);
        for(a=[45:90:315]) rotate([0,0,a]) translate([90,0,0]) {
            translate([0,0,-1]) cylinder(d=9,h=82);
            translate([0,0,73]) cylinder(d=16,h=8);
        }
        translate([-20,-126,12]) roundbox([40,25,18],3);
        translate([0,0,78])difference(){cylinder(r=108.2,h=2.2);translate([0,0,-.3])cylinder(r=97.8,h=3);}
    }
    color(orange) translate([0,0,78.05]) difference() {cylinder(r=108,h=3); translate([0,0,-1]) cylinder(r=98,h=5);}
}

// Waist enclosure and shoulder support cheeks. Shaft/bearing selection is pending.
module waist() {
    color(blue) difference() {cylinder(r=46,h=52);translate([0,0,-1])cylinder(r=15,h=54);}
    color([.76,.81,.85]) for(side=[-1,1]) difference() {
        translate([-25,side*31-4.5,27]) roundbox([50,9,35],4);
        translate([0,side*31-6,60]) ycylinder(8,12);
    }
}

// Hollow load-bearing concept shell. Geometry does not establish payload capacity.
module arm(l,r,w) {
    color(white) difference() {
        capsulebar(l,r,w);
        translate([0,0,r]) capsulebar(l-2*r,r-5,w-8);
        for(z=[0,l]) translate([0,-w/2-1,z])ycylinder(8,w+2);
        translate([r-8,-(w-14)/2,r+4])roundbox([12,w-14,l-2*r-8],3);
    }
    color(blue) translate([r-5,-(w-17)/2,r+8])roundbox([3,w-17,l-2*r-16],1);
    if(show_hardware) for(z=[0,l]) {
        color(blue) translate([0,-w/2-4,z])difference() {ycylinder(r-6,4);translate([0,-1,0])ycylinder(5,6);}
        color(orange)translate([0,-w/2-5.5,z])difference(){ycylinder(9,1.5);translate([0,-1,0])ycylinder(5,4);}
    }
}

module wrist() {
    color(blue) difference(){cylinder(r=29,h=60);translate([0,0,-1])cylinder(r=13,h=62);translate([0,-32,0])ycylinder(6,64);}
    color(orange)translate([0,0,53])difference(){cylinder(r=32,h=6);translate([0,0,-1])cylinder(r=29.2,h=8);}
}

// Palm enclosure, rear service cover and compliant contact surface.
module palm() {
    color(white) difference() {
        union() {
            difference() {
                translate([-palm_thickness/2+3,-palm_width/2,0])roundbox([palm_thickness-3,palm_width,palm_length],5);
                translate([-palm_thickness/2-1,-palm_width/2+4,4])roundbox([palm_thickness-2,palm_width-8,palm_length-9],3);
            }
            for(y=[-33,33],z=[12,87])translate([-13,y,z])xcy(4,26);
        }
        for(y=[-33,33],z=[12,87])translate([-17,y,z])xcy(1.6,36);
        translate([0,0,-2])cylinder(r=6,h=15);
        translate([-5,-45,20])roundbox([10,12,12],2);
    }
    color(blue)difference(){translate([-16,-39,3])roundbox([3,78,94],1.4);for(y=[-33,33],z=[12,87])translate([-17,y,z])xcy(1.8,5);}
    if(show_pads)color(rubber)translate([16,-26.5,19])roundbox([2,53,64],.8);
}

// Each finger segment has a root tongue, outgoing clevis, hinge bores and two guide bores.
// These bores show the design intent; a routed, tensioned tendon transmission is not solved.
module finger(l,w,distal=false) {
    d=distal?11.5:13; r=d/2; tw=w*.43; gap=tw+.9; ear=(w-gap)/2;
    color(white)difference(){
        union(){
            translate([-r,-w/2,r])roundbox([d,w,l-r-2],2.5);
            translate([0,-tw/2,0])ycylinder(r,tw);
            translate([-r+.5,-tw/2,0])roundbox([d-1,tw,r+2],1);
            if(distal)translate([0,-w/2,l-r])ycylinder(r,w);
            else {
                translate([0,-w/2,l])ycylinder(r,ear);
                translate([0,gap/2,l])ycylinder(r,ear);
            }
        }
        translate([0,-w/2-1,0])ycylinder(hinge_pin_diameter/2,w+2);
        if(!distal){
            translate([-r-1,-gap/2,l-r])cube([d+2,gap,r+2]);
            translate([0,-w/2-1,l])ycylinder(hinge_pin_diameter/2,w+2);
        }
        for(x=[-d*.3,d*.3])translate([x,0,r])cylinder(d=tendon_bore_diameter,h=max(2,l-2*r));
    }
    if(show_hardware)color(orange)translate([0,-w/2-.7,0])ycylinder(.98,w+1.4);
    if(show_pads && distal)color(rubber)translate([d/2-.3,-(w-2)/2,5])roundbox([2,w-2,max(5,l-8)],.8);
}

// A crossing-axis knuckle / thumb-opposition placeholder for mechanical development.
module yoke(thumb=false){color(blue)if(thumb)difference(){translate([0,0,-5])cylinder(r=6.8,h=10);translate([0,0,-6])cylinder(r=1.6,h=12);}else difference(){translate([-5,0,0])xcy(6.8,10);translate([-6,0,0])xcy(1.6,12);}}

module label(txt,pos,size=6){
    color(blue)translate(pos)rotate([90,0,90])linear_extrude(.5)text(txt,size=size,font="Liberation Sans",halign="left");
}

module geometry(i){
    p=robot_links[i]; kind=p[7];
    if(kind=="base")base();
    else if(kind=="waist")waist();
    else if(kind=="arm")arm(p[8],p[0]=="upper_arm"?29:24,p[0]=="upper_arm"?48:40);
    else if(kind=="wrist")wrist();
    else if(kind=="palm")palm();
    else if(kind=="yoke")yoke(p[0]=="thumb_opposition");
    else if(kind=="finger")finger(p[8],p[9],p[10]);
    if(show_labels && export_part==""){
        if(kind=="base")label("BENCH FIXTURE / M8",[125,-65,12],8);
        if(p[0]=="upper_arm")label("300 mm / UPPER ARM",[34,32,80],6);
        if(p[0]=="forearm")label("250 mm / FOREARM",[29,28,70],6);
        if(kind=="palm")label("190 mm HAND / 20 AXES",[25,46,15],5);
    }
}

function jointq(p) = pose=="zero"?0:pose=="grasp" && p[7]=="finger"?48:p[5];
module chain(i){
    p=robot_links[i];
    translate(p[2])rotate(p[3])rotate(a=jointq(p),v=p[4]){
        geometry(i);
        for(k=[0:len(robot_links)-1])if(robot_links[k][1]==i)chain(k);
    }
}
if(export_part=="" && !view_hand_only)chain(0);
else if(export_part=="" && view_hand_only)for(i=[0:len(robot_links)-1])if(robot_links[i][0]=="palm_base")chain(i);
else for(i=[0:len(robot_links)-1])if(robot_links[i][0]==export_part)geometry(i);
