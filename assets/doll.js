import * as THREE from 'three';

// ─── Scene ────────────────────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x0a1f0a, 0.032);
scene.background = new THREE.Color(0x0a1f0a);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
document.body.appendChild(renderer.domElement);

const camera = new THREE.PerspectiveCamera(52, window.innerWidth / window.innerHeight, 0.1, 200);
camera.position.set(0, 3.2, 14);
camera.lookAt(0, 2.2, 0);

// ─── Lights ───────────────────────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0x1a4a1a, 2.5));

const keyLight = new THREE.DirectionalLight(0xddffd0, 3.0);
keyLight.position.set(4, 10, 10);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(2048, 2048);
keyLight.shadow.camera.left = -20; keyLight.shadow.camera.right = 20;
keyLight.shadow.camera.top  =  20; keyLight.shadow.camera.bottom = -20;
scene.add(keyLight);

const rimLight = new THREE.DirectionalLight(0x66ffaa, 2.0);
rimLight.position.set(-5, 4, -6);
scene.add(rimLight);

const glowPt = new THREE.PointLight(0x44ff88, 1.5, 18);
scene.add(glowPt);

// ─── Floor ────────────────────────────────────────────────────────────────────
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(120, 120),
  new THREE.MeshStandardMaterial({ color: 0x0c1a0c, roughness: 0.95 })
);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);
scene.add(new THREE.GridHelper(120, 60, 0x122212, 0x0f180f));

// ─── Leaf shape (matches the rounded double-lobe leaf in image) ──────────────
// Drawn in XY plane, extruded in Z, then we set it up so the face is toward camera.
// Shape: rounded bottom, two round bumps at top (like the ref image).
function buildLeafShape() {
  const s = new THREE.Shape();

  // Apex (pointed tip) at TOP: (0, 2.2)
  // Two rounded lobes at BOTTOM — this is the slug's butt on the floor
  s.moveTo(0, 2.2);  // apex tip

  // Right side sweeping down
  s.bezierCurveTo( 0.58, 2.0,   0.85, 1.38,  0.85, 0.88);

  // Into right lower lobe
  s.bezierCurveTo( 0.85, 0.44,  0.72, 0.04,  0.45, 0.0);
  s.bezierCurveTo( 0.22, -0.04, 0.06, 0.14,  0.03, 0.30);

  // Centre notch between the two lobes
  s.bezierCurveTo( 0.01, 0.36, -0.01, 0.36, -0.03, 0.30);

  // Into left lower lobe (mirror)
  s.bezierCurveTo(-0.06, 0.14, -0.22, -0.04, -0.45, 0.0);
  s.bezierCurveTo(-0.72, 0.04, -0.85, 0.44,  -0.85, 0.88);

  // Left side back up to apex
  s.bezierCurveTo(-0.85, 1.38, -0.58, 2.0,    0.0,  2.2);

  return s;
}

const leafShape = buildLeafShape();

const extrudeSettings = {
  depth: 0.38,
  bevelEnabled: true,
  bevelThickness: 0.07,
  bevelSize: 0.07,
  bevelSegments: 5,
};

const bodyGeo = new THREE.ExtrudeGeometry(leafShape, extrudeSettings);
// Center the geometry so x=0 is mid-width, z=0 is front face center
bodyGeo.center();
// Shape: y from -0.04 (lobe bottoms) to 2.2 (apex). Total ~2.24, center ~1.08.
// After center(), bottom is at ~-1.12. Translate up so lobes sit at y=0.
bodyGeo.translate(0, 1.12, 0);

const leafMat = new THREE.MeshStandardMaterial({
  color: 0x205c20,
  roughness: 0.70,
  metalness: 0.05,
  envMapIntensity: 0.3,
});
const leafHighlightMat = new THREE.MeshStandardMaterial({
  color: 0x2a7530,
  roughness: 0.5,
  metalness: 0.0,
  transparent: true,
  opacity: 0.6,
});

// ─── Slug group ───────────────────────────────────────────────────────────────
const slug = new THREE.Group();
scene.add(slug);

// Scale up to a good screen size
slug.scale.setScalar(1.2);

// bodyPivot — we squish / lean this for slug animation
const bodyPivot = new THREE.Group();
slug.add(bodyPivot);

const bodyMesh = new THREE.Mesh(bodyGeo, leafMat);
bodyMesh.castShadow = true;
bodyPivot.add(bodyMesh);

// Subtle vein highlight (smaller leaf shape on top, slightly offset forward)
const veinGeo = new THREE.ExtrudeGeometry(buildLeafShape(), {
  depth: 0.04, bevelEnabled: false,
});
veinGeo.center();
veinGeo.translate(0, 1.12, 0);
const vein = new THREE.Mesh(veinGeo, leafHighlightMat);
vein.position.z = 0.21;   // sit on front face
vein.scale.set(0.55, 0.55, 1);
bodyPivot.add(vein);

// ─── Eyes (near top of the two lobes, ~y=1.92) ────────────────────────────────
const eyeWhiteMat = new THREE.MeshStandardMaterial({
  color: 0xffffff, roughness: 0.2, metalness: 0.05,
  emissive: 0xaaffaa, emissiveIntensity: 0.4,
});
const pupilMat = new THREE.MeshStandardMaterial({
  color: 0x0a1a0a, roughness: 0.2, metalness: 0.4,
});
const shineMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

function makeEye(xOff, yPos) {
  const g = new THREE.Group();

  const white = new THREE.Mesh(new THREE.SphereGeometry(0.10, 14, 12), eyeWhiteMat);
  g.add(white);

  const pupil = new THREE.Mesh(new THREE.SphereGeometry(0.058, 10, 8), pupilMat);
  pupil.position.z = 0.075;
  g.add(pupil);

  const shine = new THREE.Mesh(new THREE.SphereGeometry(0.018, 6, 5), shineMat);
  shine.position.set(0.025, 0.028, 0.09);
  g.add(shine);

  g.position.set(xOff, yPos, 0.22);   // on the front face of leaf
  bodyPivot.add(g);
  return g;
}

// Eyes sit just below the apex — shape is narrow there (~x ±0.18 at y≈1.95)
const eyeL = makeEye(-0.16, 1.92);
const eyeR = makeEye( 0.16, 1.92);

// ─── Arms (at ~y=1.1, out from widest part ~x=±0.82) ─────────────────────────
const branchMat = new THREE.MeshStandardMaterial({ color: 0x184a18, roughness: 0.85 });
const handMat   = new THREE.MeshStandardMaterial({
  color: 0x226622, roughness: 0.55,
  emissive: 0x0a2a0a, emissiveIntensity: 0.3,
});

function makeArm(side) {
  const shoulder = new THREE.Group();
  shoulder.position.set(side * 0.84, 0.95, 0.05);
  bodyPivot.add(shoulder);

  // Upper arm: angled outward and slightly down
  const upper = new THREE.Mesh(
    new THREE.CylinderGeometry(0.048, 0.034, 0.52, 10), branchMat
  );
  upper.castShadow = true;
  upper.rotation.z = side * (Math.PI * 0.38);  // angle ~68° outward
  upper.position.set(side * 0.20, -0.04, 0);
  shoulder.add(upper);

  // Elbow group hangs from tip of upper arm
  const elbow = new THREE.Group();
  elbow.position.set(side * 0.42, -0.09, 0);
  shoulder.add(elbow);

  const lower = new THREE.Mesh(
    new THREE.CylinderGeometry(0.034, 0.024, 0.40, 10), branchMat
  );
  lower.castShadow = true;
  lower.rotation.z = side * 0.4;
  lower.position.set(side * 0.14, -0.10, 0);
  elbow.add(lower);

  // Hand bud
  const hand = new THREE.Mesh(new THREE.SphereGeometry(0.09, 12, 10), handMat);
  hand.position.set(side * 0.30, -0.22, 0);
  elbow.add(hand);

  // 3 tiny finger nubs
  for (let i = 0; i < 3; i++) {
    const nub = new THREE.Mesh(new THREE.SphereGeometry(0.03, 6, 5), handMat);
    const a = (i - 1) * 0.55;
    nub.position.set(
      hand.position.x + side * 0.07,
      hand.position.y + Math.sin(a) * 0.05,
      hand.position.z + Math.cos(a) * 0.06
    );
    elbow.add(nub);
  }

  return { shoulder, elbow };
}

const armL = makeArm(-1);
const armR = makeArm( 1);

// ─── Ground blob shadow ───────────────────────────────────────────────────────
const blobGeo = new THREE.CircleGeometry(0.55, 24);
const blobMat = new THREE.MeshBasicMaterial({
  color: 0x000000, transparent: true, opacity: 0.30, depthWrite: false,
});
const blob = new THREE.Mesh(blobGeo, blobMat);
blob.rotation.x = -Math.PI / 2;
blob.position.y = 0.015 / 1.2;
slug.add(blob);

// ─── Slug trail glow ──────────────────────────────────────────────────────────
const trailMat = new THREE.MeshBasicMaterial({
  color: 0x44ff88, transparent: true, opacity: 0.07, depthWrite: false,
});
const trail = new THREE.Mesh(new THREE.PlaneGeometry(1, 2.5), trailMat);
trail.rotation.x = -Math.PI / 2;
trail.position.set(0, 0.02 / 1.2, 0);
slug.add(trail);

// ─── Bg particles ─────────────────────────────────────────────────────────────
const pc = 500;
const pp = new Float32Array(pc * 3);
for (let i = 0; i < pc; i++) {
  pp[i*3]   = (Math.random() - 0.5) * 90;
  pp[i*3+1] = Math.random() * 20;
  pp[i*3+2] = (Math.random() - 0.5) * 90;
}
const pGeo = new THREE.BufferGeometry();
pGeo.setAttribute('position', new THREE.BufferAttribute(pp, 3));
scene.add(new THREE.Points(pGeo, new THREE.PointsMaterial({
  color: 0x55ff99, size: 0.06, transparent: true, opacity: 0.3,
})));

// ─── Locomotion settings ──────────────────────────────────────────────────────
const SPEED      = 2.0;   // units / sec
const FREQ       = 1.1;   // slug cycles / sec
const SQUISH_Y   = 0.12;
const SWELL_XZ   = 0.08;
const LEAN_SIDE  = 0.18;  // tilt toward travel direction (rad)
const TRACK      = 13;    // half track length

let t = 0, posX = -TRACK;
let dir = 1;                // +1 right, -1 left
let camTheta = 0, camTarget = 0;

window.addEventListener('mousemove', e => {
  camTarget = ((e.clientX / window.innerWidth) - 0.5) * 1.0;
});
window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ─── Render loop ──────────────────────────────────────────────────────────────
let prev = performance.now();

function animate(now) {
  requestAnimationFrame(animate);
  const dt = Math.min((now - prev) / 1000, 0.05);
  prev = now;
  t += dt;

  const cycle = t * FREQ * Math.PI * 2;
  // contract: 0 = extended (leaning, fast), 1 = contracted (squished, slow)
  const contract = 0.5 - 0.5 * Math.cos(cycle);

  // ── Position ───────────────────────────────────────────────────────────────
  const speedFactor = 0.35 + 0.65 * (1 - contract);
  posX += SPEED * dir * speedFactor * dt;

  if (posX > TRACK)  { posX =  TRACK; dir = -1; }
  if (posX < -TRACK) { posX = -TRACK; dir =  1; }

  slug.position.set(posX, 0, 0);

  // Leaf always faces the camera (no y-rotation on the slug group itself)
  // Tilt toward direction of travel
  bodyPivot.rotation.z = -dir * LEAN_SIDE * (1 - contract);

  // ── Body squish (slug compress/extend) ────────────────────────────────────
  bodyPivot.scale.y  = 1.0 - contract * SQUISH_Y;
  bodyPivot.scale.x  = 1.0 + contract * SWELL_XZ;
  bodyPivot.scale.z  = 1.0 + contract * SWELL_XZ;

  // Slight vertical hop at peak extension (just before contraction)
  const hop = Math.max(0, Math.sin(cycle)) * 0.06;
  bodyPivot.position.y = hop;

  // ── Arms wave ──────────────────────────────────────────────────────────────
  const armWave = Math.sin(cycle) * 0.28;
  armL.shoulder.rotation.z =  armWave * 0.5;
  armR.shoulder.rotation.z = -armWave * 0.5;
  armL.elbow.rotation.z    =  0.2 + Math.sin(cycle + 0.8) * 0.25;
  armR.elbow.rotation.z    = -0.2 - Math.sin(cycle + 0.8) * 0.25;

  // ── Eyes blink ────────────────────────────────────────────────────────────
  const blinkPhase = (t % 3.2) / 3.2;
  const blink = blinkPhase > 0.91 ? Math.max(0.1, 1 - (blinkPhase - 0.91) * 30) : 1.0;
  eyeL.scale.y = blink;
  eyeR.scale.y = blink;

  // Eyes look in direction of travel (slight rotate)
  eyeL.rotation.y = dir * 0.15;
  eyeR.rotation.y = dir * 0.15;

  // ── Trail ─────────────────────────────────────────────────────────────────
  trail.scale.x = 0.7 + contract * 0.6;
  trail.position.x = -dir * (1 - contract) * 0.5;
  trail.material.opacity = 0.04 + (1 - contract) * 0.09;

  // Blob shadow squishes with body
  blob.scale.set(1 + contract * 0.2, 1, 1 + contract * 0.2);

  // ── Glow follows slug ──────────────────────────────────────────────────────
  glowPt.position.set(posX + dir * 1.5, 3, 2);
  glowPt.intensity = 1.0 + contract * 0.8;

  // ── Camera ────────────────────────────────────────────────────────────────
  camTheta += (camTarget - camTheta) * 0.04;
  camera.position.x = posX + Math.sin(camTheta) * 13;
  camera.position.z = Math.cos(camTheta) * 13;
  camera.position.y = 3.2;
  camera.lookAt(posX, 2.2, 0);

  renderer.render(scene, camera);
}

requestAnimationFrame(animate);
