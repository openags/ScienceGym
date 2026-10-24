// One global simulation clock across independently downloadable video chapters.
export class RecordedPlayback {
  constructor(video, controls, download) {
    this.video=video;this.download=download;this.generation=0;this.chapters=[];this.index=-1;
    this.select=document.createElement('select');this.select.setAttribute('aria-label','Playback chapter');
    this.range=document.createElement('input');this.range.type='range';this.range.min=0;this.range.step=.01;this.range.setAttribute('aria-label','Simulation time');
    this.clock=document.createElement('output');this.clock.setAttribute('aria-live','off');
    controls.append(this.select,this.range,this.clock);
    this.select.onchange=()=>this.seek(this.chapters[Number(this.select.value)].start_s);
    this.range.oninput=()=>this.seek(Number(this.range.value));
    video.addEventListener('timeupdate',()=>this.update());
    video.addEventListener('ended',()=>{if(this.index+1<this.chapters.length)this.open(this.index+1,0,true);});
  }
  reset() {
    this.generation++;this.video.pause();this.video.removeAttribute('src');this.video.load();
    this.index=-1;this.chapters=[];this.select.replaceChildren();this.range.value=0;this.clock.textContent='';
  }
  load(base, chapters, duration) {
    this.reset();this.base=base;this.duration=duration;
    if(!chapters.length||!Number.isFinite(duration)||duration<=0)throw new Error('Invalid playback duration');
    for(let i=0;i<chapters.length;i++) {
      const c=chapters[i];
      if(!/^[a-zA-Z0-9_./-]+\.mp4$/.test(c.path)||c.path.split('/').includes('..')||c.path.startsWith('/')||!Number.isFinite(c.start_s)||c.start_s<0)throw new Error('Invalid playback chapter');
      if(i===0&&Math.abs(c.start_s)>.001)throw new Error('Playback must start at zero');
      if(i&&Math.abs(chapters[i-1].end_s-c.start_s)>.1)throw new Error('Gap between playback chapters');
      const option=document.createElement('option');option.value=i;option.textContent=`Chapter ${i+1} / ${chapters.length}`;this.select.append(option);
    }
    this.chapters=chapters;this.range.max=duration;this.select.hidden=chapters.length===1;this.open(0,0,false);
  }
  open(index, localTime, play) {
    const chapter=this.chapters[index],token=++this.generation;this.index=index;this.select.value=index;
    this.video.pause();this.video.src=this.base+chapter.path;this.download.href=this.video.src;
    this.video.addEventListener('loadedmetadata',()=>{
      if(token!==this.generation)return;
      this.video.currentTime=Math.min(localTime,Math.max(0,this.video.duration-.001));this.update();
      if(play)this.video.play().catch(()=>{});
    },{once:true});this.video.load();this.update();
  }
  seek(time) {
    if(!this.chapters.length)return;
    time=Math.max(0,Math.min(time,this.duration));
    let index=this.chapters.findLastIndex(c=>c.start_s<=time);index=Math.max(0,index);
    if(index===this.index&&this.video.readyState>=1){this.video.currentTime=Math.min(time-this.chapters[index].start_s,this.video.duration-.001);this.update();}
    else this.open(index,time-this.chapters[index].start_s,!this.video.paused);
  }
  update() {
    if(this.index<0)return;
    const time=Math.min(this.duration,this.chapters[this.index].start_s+(this.video.currentTime||0));
    this.range.value=time;this.clock.textContent=`${time.toFixed(2)} / ${this.duration.toFixed(2)} s`;
    this.video.dataset.simulationTime=String(time);this.video.dataset.chapter=String(this.index+1);
  }
}
