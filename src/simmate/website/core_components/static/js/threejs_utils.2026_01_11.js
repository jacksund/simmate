import * as THREE from 'three';
import { TrackballControls } from 'three/addons/controls/TrackballControls.js';

const ELEMENT_COLORS_JMOL = {
    "H": 0xFFFFFF, 
    "He": 0xD9FFFF, 
    "Li": 0xCC80FF, 
    "Be": 0xC2FF00, 
    "B": 0xFFB5B5, 
    "C": 0x909090, 
    "N": 0x3050F8, 
    "O": 0xFF0D0D, 
    "F": 0x90E050, 
    "Ne": 0xB3E3F5, 
    "Na": 0xAB5CF2, 
    "Mg": 0x8AFF00, 
    "Al": 0xBFA6A6, 
    "Si": 0xF0C8A0, 
    "P": 0xFF8000, 
    "S": 0xFFFF30, 
    "Cl": 0x1FF01F, 
    "Ar": 0x80D1E3, 
    "K": 0x8F40D4, 
    "Ca": 0x3DFF00, 
    "Sc": 0xE6E6E6, 
    "Ti": 0xBFC2C7, 
    "V": 0xA6A6AB, 
    "Cr": 0x8A99C7, 
    "Mn": 0x9C7AC7, 
    "Fe": 0xE06633, 
    "Co": 0xF090A0, 
    "Ni": 0x50D050, 
    "Cu": 0xC88033, 
    "Zn": 0x7D80B0, 
    "Ga": 0xC28F8F, 
    "Ge": 0x668F8F, 
    "As": 0xBD80E3, 
    "Se": 0xFFA100, 
    "Br": 0xA62929, 
    "Kr": 0x5CB8D1, 
    "Rb": 0x702EB0, 
    "Sr": 0x00FF00, 
    "Y": 0x94FFFF, 
    "Zr": 0x94E0E0, 
    "Nb": 0x73C2C9, 
    "Mo": 0x54B5B5, 
    "Tc": 0x3B9E9E, 
    "Ru": 0x248F8F, 
    "Rh": 0x0A7D8C, 
    "Pd": 0x006985, 
    "Ag": 0xC0C0C0, 
    "Cd": 0xFFD98F, 
    "In": 0xA67573, 
    "Sn": 0x668080, 
    "Sb": 0x9E63B5, 
    "Te": 0xD47A00, 
    "I": 0x940094, 
    "Xe": 0x429EB0, 
    "Cs": 0x57178F, 
    "Ba": 0x00C900, 
    "La": 0x70D4FF, 
    "Ce": 0xFFFFC7, 
    "Pr": 0xD9FFC7, 
    "Nd": 0xC7FFC7, 
    "Pm": 0xA3FFC7, 
    "Sm": 0x8FFFC7, 
    "Eu": 0x61FFC7, 
    "Gd": 0x45FFC7, 
    "Tb": 0x30FFC7, 
    "Dy": 0x1FFFC7, 
    "Ho": 0x00FF9C, 
    "Er": 0x00E675, 
    "Tm": 0x00D452, 
    "Yb": 0x00BF38, 
    "Lu": 0x00AB24, 
    "Hf": 0x4DC2FF, 
    "Ta": 0x4DA6FF, 
    "W": 0x2194D6, 
    "Re": 0x267DAB, 
    "Os": 0x266696, 
    "Ir": 0x175487, 
    "Pt": 0xD0D0E0, 
    "Au": 0xFFD123, 
    "Hg": 0xB8B8D0, 
    "Tl": 0xA6544D, 
    "Pb": 0x575961, 
    "Bi": 0x9E4FB5, 
    "Po": 0xAB5C00, 
    "At": 0x754F45, 
    "Rn": 0x428296, 
    "Fr": 0x420066, 
    "Ra": 0x007D00, 
    "Ac": 0x70ABFA, 
    "Th": 0x00BAFF, 
    "Pa": 0x00A1FF, 
    "U": 0x008FFF, 
    "Np": 0x0080FF, 
    "Pu": 0x006BFF, 
    "Am": 0x545CF2, 
    "Cm": 0x785CE3, 
    "Bk": 0x8A4FE3, 
    "Cf": 0xA136D4, 
    "Es": 0xB31FD4, 
    "Fm": 0xB31FBA, 
    "Md": 0xB30DA6, 
    "No": 0xBD0D87, 
    "Lr": 0xC70066, 
    "Rf": 0xCC0059, 
    "Db": 0xD1004F, 
    "Sg": 0xD90045, 
    "Bh": 0xE00038, 
    "Hs": 0xE6002E, 
    "Mt": 0xEB0026,
};


// Creates a 3D structure/molecule viewport in ThreeJS
function add_threejs_render(target_div_id, data) {
    const container = document.getElementById(target_div_id);
    
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff);
    scene.fog = new THREE.Fog(0xffffff, 20, 100);

    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(20, 10, 20);
    camera.up.set(0, 0, 1);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    const controls = new TrackballControls(camera, renderer.domElement);
    controls.rotateSpeed = 3.0;

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.0);
    dirLight.position.set(5, 10, 7);
    camera.add(dirLight); 
    scene.add(camera);

    const crystalGroup = new THREE.Group();
    const sphereGeo = new THREE.IcosahedronGeometry(1, 4);
    const outlineMat = new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.BackSide });

    const atomPositions = data.atoms.map(([symbol, radius, coords]) => {
        const group = new THREE.Group();
        const mat = new THREE.MeshStandardMaterial({ color: ELEMENT_COLORS_JMOL[symbol], metalness: 0.1, roughness: 0.5 });
        const mesh = new THREE.Mesh(sphereGeo, mat);
        mesh.scale.setScalar(radius * 0.75);
        const outline = new THREE.Mesh(sphereGeo, outlineMat);
        outline.scale.setScalar(radius * 0.75 + 0.04);
        group.add(mesh, outline);
        group.position.set(...coords);
        crystalGroup.add(group);
        return new THREE.Vector3(...coords);
    });

    const bondMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
    data.bonds.forEach(([iA, iB]) => {
        const start = atomPositions[iA], end = atomPositions[iB];
        const vec = new THREE.Vector3().subVectors(end, start);
        const bondGeo = new THREE.CylinderGeometry(0.08, 0.08, vec.length(), 8);
        const bond = new THREE.Mesh(bondGeo, bondMat);
        bond.position.copy(start).add(vec.clone().multiplyScalar(0.5));
        bond.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), vec.clone().normalize());
        crystalGroup.add(bond);
    });

    const v = data.lattice.map(l => new THREE.Vector3(...l));
    const corners = [
        new THREE.Vector3(0,0,0), v[2], v[0], v[0].clone().add(v[2]),
        v[1], v[1].clone().add(v[2]), v[0].clone().add(v[1]), v[0].clone().add(v[1]).add(v[2])
    ];
    const edges = [[0,2], [2,6], [6,4], [4,0], [1,3], [3,7], [7,5], [5,1], [0,1], [2,3], [6,7], [4,5]];
    
    edges.forEach(([s, e]) => {
        const path = new THREE.LineCurve3(corners[s], corners[e]);
        crystalGroup.add(new THREE.Mesh(new THREE.TubeGeometry(path, 1, 0.02, 6, false), new THREE.MeshBasicMaterial({ color: 0xbbbbbb })));
    });

    const box = new THREE.Box3().setFromObject(crystalGroup);
    crystalGroup.position.sub(box.getCenter(new THREE.Vector3()));
    scene.add(crystalGroup);

    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    });
};

// since this is a module, we this to make it publically available
window.add_threejs_render = add_threejs_render;
