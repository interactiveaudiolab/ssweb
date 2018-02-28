function getMelScatterSpectrogramAsImage(heatmap, duration, freqMax) {
    let url = "./mel_spec_image?val=" + Math.random().toString(36).substring(7);
    // duration currently hardcoded in for toy data
    heatmap.drawImage(url, duration, freqMax);
}

function getSpectrogramAsImage(heatmap, duration, freqMax) {
    let url = "./spec_image?val=" + Math.random().toString(36).substring(7);
    // let duration = mixture_waveform.backend.getDuration();

    heatmap.drawImage(url, duration, freqMax);
    enableTools(true, '.spec-tool');
}


class ScatterSpectrogram extends PlotlyHeatmap {
    constructor(divID, yMax) {
        super(divID, yMax);
        this.audioLength = null;
        this.freqMax = null;

        this.plotLayout.hovermode = false;

        this.plotLayout.xaxis = {
            title: "Time (s)",
            type: "linear",
            range: [0.0, 1.0],
            showgrid: false
        };

        this.plotLayout.yaxis = {
            title: "Frequency (Mel)",
            type: "linear",
            autorange: true,
            range: [0.0, 150],
            showgrid: false
        };

        this.plotLayout

        this.DOMObject.on('plotly_selected', (eventData, data) => {
            if(!data || !data.range) { this.clearMarkers(); }
        });

        this.emptyHeatmap();
    }

    clearMarkers() {
        let data = [{x:[], y:[]}];
        this.plot = Plotly.newPlot(this.divID, data, this.plotLayout, this.plotOptions);
    }

    addMarkers(x_marks, y_marks, color) {
        // let data = [{x:[], y:[], type:'scattergl',
        //         mode:'markers', marker: { symbol: "square", size:5, color: '#ffffff', opacity: 1 }}];
        Plotly.addTraces(spectrogram.divID, { x: x_marks, y: y_marks, type: 'scattergl',
            mode:'markers', marker: { size: 2, color: (color !== undefined ? color : '#ffffff'), opacity: 1 }});
    }

    drawImage(url, duration, freqMax) {
        this.plotLayout.xaxis.range = [0.0, duration];
        this.plotLayout.yaxis.range = [0.0, freqMax];
        this.plotLayout.yaxis.autorange = false;
        this.plotLayout.images = [{
            "source": url,
            "xref": "x",
            "yref": "y",
            "x": 0,
            "y": 0,
            "sizex": duration,
            "sizey": freqMax,
            "xanchor": "left",
            "yanchor": "bottom",
            "sizing": "stretch",
            "layer": "below"
        }];

        let data = [{x:[], y:[]}];
        this.plot = Plotly.newPlot(this.divID, data, this.plotLayout, this.plotOptions);
    }
}