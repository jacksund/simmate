import * as THREE from 'three';
import { TrackballControls } from 'three/addons/controls/TrackballControls.js';


// Creates a 3D structure/molecule viewport in ThreeJS
function add_threejs_render(target_div_id, data) {
    
    // if we have a str then it is JSON, otherwise we already have a dict
    data = typeof data === 'string' ? JSON.parse(data) : data;
    
    const container = document.getElementById(target_div_id);
    
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xffffff);
    scene.fog = new THREE.Fog(0xffffff, 20, 100);

    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(15, 5, 10);
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

    const atomPositions = data.atoms.map(([e_color, radius, coords]) => {
        const group = new THREE.Group();
        const mat = new THREE.MeshStandardMaterial({ color: e_color, metalness: 0.1, roughness: 0.5 });
        const mesh = new THREE.Mesh(sphereGeo, mat);
        mesh.scale.setScalar(radius * 0.75);
        const outline = new THREE.Mesh(sphereGeo, outlineMat);
        outline.scale.setScalar(radius * 0.75 + 0.06);
        group.add(mesh, outline);
        group.position.set(...coords);
        crystalGroup.add(group);
        return new THREE.Vector3(...coords);
    });

    const bondMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
    data.bonds.forEach(([iA, iB]) => {
        const start = atomPositions[iA], end = atomPositions[iB];
        const vec = new THREE.Vector3().subVectors(end, start);
        const bondGeo = new THREE.CylinderGeometry(0.12, 0.12, vec.length(), 8);
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
