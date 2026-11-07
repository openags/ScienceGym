// Exact source-triangle distance for the selected PIKE panel reconstruction.
// The generated header contains the unchanged closed surface, its BVH, and
// validated convex-outer/polygonal-through-bore occupancy planes.
// This plugin supplies collision geometry only; it cannot apply forces or
// inspect or control the robot. MuJoCo performs all contact dynamics.
#include <algorithm>
#include <cmath>
#include <limits>
#include <mujoco/mjplugin.h>
#include <mujoco/mujoco.h>

namespace {
struct Vec { double x, y, z; };
struct Node { Vec lo, hi; int left, right, first, count; };
Vec operator+(Vec a, Vec b) { return {a.x+b.x, a.y+b.y, a.z+b.z}; }
Vec operator-(Vec a, Vec b) { return {a.x-b.x, a.y-b.y, a.z-b.z}; }
Vec operator*(Vec a, double s) { return {a.x*s, a.y*s, a.z*s}; }
double dot(Vec a, Vec b) { return a.x*b.x+a.y*b.y+a.z*b.z; }

#include "pike_surface_geometry.h"

Vec segment(Vec p, Vec a, Vec b) {
  Vec v=b-a;
  double t=std::clamp(dot(p-a,v)/dot(v,v),0.,1.);
  return a+v*t;
}

Vec closest_triangle(Vec p, int i) {
  Vec a=kTriangles[i][0], b=kTriangles[i][1], c=kTriangles[i][2];
  Vec ab=b-a, ac=c-a, ap=p-a;
  double aa=dot(ab,ab), bb=dot(ac,ac), cross=dot(ab,ac);
  double denominator=aa*bb-cross*cross;
  double u=(dot(ap,ab)*bb-dot(ap,ac)*cross)/denominator;
  double v=(dot(ap,ac)*aa-dot(ap,ab)*cross)/denominator;
  if (u>=0. && v>=0. && u+v<=1.) return a+ab*u+ac*v;
  Vec q=segment(p,a,b), r=segment(p,b,c), s=segment(p,c,a);
  double dq=dot(p-q,p-q), dr=dot(p-r,p-r), ds=dot(p-s,p-s);
  return dq<=dr && dq<=ds ? q : (dr<=ds ? r : s);
}

double box_distance_squared(Vec p, const Node& node) {
  double x=std::max({node.lo.x-p.x,0.,p.x-node.hi.x});
  double y=std::max({node.lo.y-p.y,0.,p.y-node.hi.y});
  double z=std::max({node.lo.z-p.z,0.,p.z-node.hi.z});
  return x*x+y*y+z*z;
}

struct Nearest { double squared=std::numeric_limits<double>::infinity(); Vec point{}; int face=-1; };
void nearest(Vec p, int id, Nearest& best) {
  const Node& node=kNodes[id];
  if (box_distance_squared(p,node)>best.squared) return;
  if (node.count) {
    for (int i=node.first; i<node.first+node.count; ++i) {
      Vec q=closest_triangle(p,i);
      double squared=dot(p-q,p-q);
      if (squared<best.squared) best={squared,q,i};
    }
  } else {
    int a=node.left, b=node.right;
    if (box_distance_squared(p,kNodes[a])>box_distance_squared(p,kNodes[b])) std::swap(a,b);
    nearest(p,a,best); nearest(p,b,best);
  }
}

bool contains(Vec p) {
  Vec world{
    kRotation[0][0]*p.x+kRotation[0][1]*p.y+kRotation[0][2]*p.z+kTranslation[0],
    kRotation[1][0]*p.x+kRotation[1][1]*p.y+kRotation[1][2]*p.z+kTranslation[1],
    kRotation[2][0]*p.x+kRotation[2][1]*p.y+kRotation[2][2]*p.z+kTranslation[2]};
  for (const auto& plane:kOuterPlanes)
    if (plane[0]*world.x+plane[1]*world.y+plane[2]*world.z+plane[3]>0.) return false;
  if (world.z<=kBoreFloor) return true;
  for (const auto& plane:kBorePlanes)
    if (plane[0]*world.x+plane[1]*world.y+plane[2]>0.) return true;
  return false;
}

double distance(const mjtNum* point) {
  Vec p{point[0],point[1],point[2]}; Nearest best; nearest(p,0,best);
  return std::sqrt(best.squared)*(contains(p) ? -1. : 1.);
}

void gradient(mjtNum* result, const mjtNum* point) {
  Vec p{point[0],point[1],point[2]}; Nearest best; nearest(p,0,best);
  double length=std::sqrt(best.squared);
  Vec normal=length>1e-14 ? (p-best.point)*((contains(p) ? -1. : 1.)/length)
                         : kFaceNormals[best.face];
  result[0]=normal.x; result[1]=normal.y; result[2]=normal.z;
}
}  // namespace

mjPLUGIN_LIB_INIT(sciencegym_pike_panel) {
  mjpPlugin plugin;
  mjp_defaultPlugin(&plugin);
  plugin.name=kPluginName;
  plugin.capabilityflags=mjPLUGIN_SDF;
  plugin.nattribute=0;
  plugin.nstate=+[](const mjModel*,int) {return 0;};
  plugin.init=+[](const mjModel*,mjData*,int) {return 0;};
  plugin.reset=+[](const mjModel*,mjtNum*,void*,int) {};
  plugin.compute=+[](const mjModel*,mjData*,int,int) {};
  plugin.sdf_distance=+[](const mjtNum* p,const mjData*,int) {return distance(p);};
  plugin.sdf_gradient=+[](mjtNum* g,const mjtNum* p,const mjData*,int) {gradient(g,p);};
  plugin.sdf_staticdistance=+[](const mjtNum* p,const mjtNum*) {return distance(p);};
  plugin.sdf_attribute=+[](mjtNum*,const char**,const char**) {};
  plugin.sdf_aabb=+[](mjtNum* box,const mjtNum*) {
    box[0]=(kNodes[0].lo.x+kNodes[0].hi.x)/2.;
    box[1]=(kNodes[0].lo.y+kNodes[0].hi.y)/2.;
    box[2]=(kNodes[0].lo.z+kNodes[0].hi.z)/2.;
    box[3]=(kNodes[0].hi.x-kNodes[0].lo.x)/2.;
    box[4]=(kNodes[0].hi.y-kNodes[0].lo.y)/2.;
    box[5]=(kNodes[0].hi.z-kNodes[0].lo.z)/2.;
  };
  mjp_registerPlugin(&plugin);
}
